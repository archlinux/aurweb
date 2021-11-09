import functools
import re

from datetime import datetime
from http import HTTPStatus

import fastapi

from fastapi.responses import RedirectResponse
from sqlalchemy import and_
from starlette.authentication import AuthCredentials, AuthenticationBackend
from starlette.requests import HTTPConnection

import aurweb.config

from aurweb import l10n, util
from aurweb.models import Session, User
from aurweb.models.account_type import ACCOUNT_TYPE_ID
from aurweb.templates import make_variable_context, render_template


class StubQuery:
    """ Acts as a stubbed version of an orm.Query. Typically used
    to masquerade fake records for an AnonymousUser. """

    def filter(self, *args):
        return StubQuery()

    def scalar(self):
        return 0


class AnonymousUser:
    """ A stubbed User class used when an unauthenticated User
    makes a request against FastAPI. """
    # Stub attributes used to mimic a real user.
    ID = 0

    class AccountType:
        """ A stubbed AccountType static class. In here, we use an ID
        and AccountType which do not exist in our constant records.
        All records primary keys (AccountType.ID) should be non-zero,
        so using a zero here means that we'll never match against a
        real AccountType. """
        ID = 0
        AccountType = "Anonymous"

    # AccountTypeID == AccountType.ID; assign a stubbed column.
    AccountTypeID = AccountType.ID

    LangPreference = aurweb.config.get("options", "default_lang")
    Timezone = aurweb.config.get("options", "default_timezone")

    Suspended = 0
    InactivityTS = 0

    # A stub ssh_pub_key relationship.
    ssh_pub_key = None

    # Add stubbed relationship backrefs.
    notifications = StubQuery()
    package_votes = StubQuery()

    # A nonce attribute, needed for all browser sessions; set in __init__.
    nonce = None

    def __init__(self):
        self.nonce = util.make_nonce()

    @staticmethod
    def is_authenticated():
        return False

    @staticmethod
    def is_trusted_user():
        return False

    @staticmethod
    def is_developer():
        return False

    @staticmethod
    def is_elevated():
        return False

    @staticmethod
    def has_credential(credential, **kwargs):
        return False

    @staticmethod
    def voted_for(package):
        return False

    @staticmethod
    def notified(package):
        return False


class BasicAuthBackend(AuthenticationBackend):
    async def authenticate(self, conn: HTTPConnection):
        from aurweb.db import session

        sid = conn.cookies.get("AURSID")
        if not sid:
            return (None, AnonymousUser())

        now_ts = datetime.utcnow().timestamp()
        record = session.query(Session).filter(
            and_(Session.SessionID == sid,
                 Session.LastUpdateTS >= now_ts)).first()

        # If no session with sid and a LastUpdateTS now or later exists.
        if not record:
            return (None, AnonymousUser())

        # At this point, we cannot have an invalid user if the record
        # exists, due to ForeignKey constraints in the schema upheld
        # by mysqlclient.
        user = session.query(User).filter(User.ID == record.UsersID).first()
        user.nonce = util.make_nonce()
        user.authenticated = True

        return (AuthCredentials(["authenticated"]), user)


def auth_required(is_required: bool = True,
                  login: bool = True,
                  redirect: str = "/",
                  template: tuple = None,
                  status_code: HTTPStatus = HTTPStatus.UNAUTHORIZED):
    """ Authentication route decorator.

    If redirect is given, the user will be redirected if the auth state
    does not match is_required.

    If template is given, it will be rendered with Unauthorized if
    is_required does not match and take priority over redirect.

    A precondition of this function is that, if template is provided,
    it **must** match the following format:

        template=("template.html", ["Some Template For", "{}"], ["username"])

    Where `username` is a FastAPI request path parameter, fitting
    a route like: `/some_route/{username}`.

    If you wish to supply a non-formatted template, just omit any Python
    format strings (with the '{}' substring). The third tuple element
    will not be used, and so anything can be supplied.

        template=("template.html", ["Some Page"], None)

    All title shards and format parameters will be translated before
    applying any format operations.

    :param is_required: A boolean indicating whether the function requires auth
    :param login: Redirect to `/login`, passing `next=<redirect>`
    :param redirect: Path to redirect to if is_required isn't True
    :param template: A three-element template tuple:
                     (path, title_iterable, variable_iterable)
    :param status_code: An optional status_code for template render.
                        Redirects are always SEE_OTHER.
    """

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(request, *args, **kwargs):
            if request.user.is_authenticated() != is_required:
                url = "/"

                if redirect:
                    path_params_expr = re.compile(r'\{(\w+)\}')
                    match = re.findall(path_params_expr, redirect)
                    args = {k: request.path_params.get(k) for k in match}
                    url = redirect.format(**args)

                    if login:
                        url = "/login?" + util.urlencode({"next": url})

                if template:
                    # template=("template.html",
                    #           ["Some Title", "someFormatted {}"],
                    #           ["variable"])
                    # => render template.html with title:
                    #    "Some Title someFormatted variables"
                    path, title_parts, variables = template
                    _ = l10n.get_translator_for_request(request)

                    # Step through title_parts; for each part which contains
                    # a '{}' in it, apply .format(var) where var = the current
                    # iteration of variables.
                    #
                    # This implies that len(variables) is equal to
                    # len([part for part in title_parts if '{}' in part])
                    # and this must always be true.
                    #
                    sanitized = []
                    _variables = iter(variables)
                    for part in title_parts:
                        if "{}" in part:  # If this part is formattable.
                            key = next(_variables)
                            var = request.path_params.get(key)
                            sanitized.append(_(part.format(var)))
                        else:  # Otherwise, just add the translated part.
                            sanitized.append(_(part))

                    # Glue all title parts together, separated by spaces.
                    title = " ".join(sanitized)

                    context = await make_variable_context(request, title)
                    return render_template(request, path, context,
                                           status_code=status_code)
                return RedirectResponse(url,
                                        status_code=int(HTTPStatus.SEE_OTHER))
            return await func(request, *args, **kwargs)
        return wrapper

    return decorator


def account_type_required(one_of: set):
    """ A decorator that can be used on FastAPI routes to dictate
    that a user belongs to one of the types defined in one_of.

    This decorator should be run after an @auth_required(True) is
    dictated.

    - Example code:

    @router.get('/some_route')
    @auth_required(True)
    @account_type_required({"Trusted User", "Trusted User & Developer"})
    async def some_route(request: fastapi.Request):
        return Response()

    :param one_of: A set consisting of strings to match against AccountType.
    :return: Return the FastAPI function this decorator wraps.
    """
    # Convert any account type string constants to their integer IDs.
    one_of = {
        ACCOUNT_TYPE_ID[atype]
        for atype in one_of
        if isinstance(atype, str)
    }

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(request: fastapi.Request, *args, **kwargs):
            if request.user.AccountType.ID not in one_of:
                return RedirectResponse("/",
                                        status_code=int(HTTPStatus.SEE_OTHER))
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator


CRED_ACCOUNT_CHANGE_TYPE = 1
CRED_ACCOUNT_EDIT = 2
CRED_ACCOUNT_EDIT_DEV = 3
CRED_ACCOUNT_LAST_LOGIN = 4
CRED_ACCOUNT_SEARCH = 5
CRED_ACCOUNT_LIST_COMMENTS = 28
CRED_COMMENT_DELETE = 6
CRED_COMMENT_UNDELETE = 27
CRED_COMMENT_VIEW_DELETED = 22
CRED_COMMENT_EDIT = 25
CRED_COMMENT_PIN = 26
CRED_PKGBASE_ADOPT = 7
CRED_PKGBASE_SET_KEYWORDS = 8
CRED_PKGBASE_DELETE = 9
CRED_PKGBASE_DISOWN = 10
CRED_PKGBASE_EDIT_COMAINTAINERS = 24
CRED_PKGBASE_FLAG = 11
CRED_PKGBASE_LIST_VOTERS = 12
CRED_PKGBASE_NOTIFY = 13
CRED_PKGBASE_UNFLAG = 15
CRED_PKGBASE_VOTE = 16
CRED_PKGREQ_FILE = 23
CRED_PKGREQ_CLOSE = 17
CRED_PKGREQ_LIST = 18
CRED_TU_ADD_VOTE = 19
CRED_TU_LIST_VOTES = 20
CRED_TU_VOTE = 21
CRED_PKGBASE_MERGE = 29


def has_any(user, *account_types):
    return str(user.AccountType) in set(account_types)


def user_developer_or_trusted_user(user):
    return True


def trusted_user(user):
    return has_any(user, "Trusted User", "Trusted User & Developer")


def developer(user):
    return has_any(user, "Developer", "Trusted User & Developer")


def trusted_user_or_dev(user):
    return has_any(user, "Trusted User", "Developer",
                   "Trusted User & Developer")


# A mapping of functions that users must pass to have credentials.
cred_filters = {
    CRED_PKGBASE_FLAG: user_developer_or_trusted_user,
    CRED_PKGBASE_NOTIFY: user_developer_or_trusted_user,
    CRED_PKGBASE_VOTE: user_developer_or_trusted_user,
    CRED_PKGREQ_FILE: user_developer_or_trusted_user,
    CRED_ACCOUNT_CHANGE_TYPE: trusted_user_or_dev,
    CRED_ACCOUNT_EDIT: trusted_user_or_dev,
    CRED_ACCOUNT_LAST_LOGIN: trusted_user_or_dev,
    CRED_ACCOUNT_LIST_COMMENTS: trusted_user_or_dev,
    CRED_ACCOUNT_SEARCH: trusted_user_or_dev,
    CRED_COMMENT_DELETE: trusted_user_or_dev,
    CRED_COMMENT_UNDELETE: trusted_user_or_dev,
    CRED_COMMENT_VIEW_DELETED: trusted_user_or_dev,
    CRED_COMMENT_EDIT: trusted_user_or_dev,
    CRED_COMMENT_PIN: trusted_user_or_dev,
    CRED_PKGBASE_ADOPT: trusted_user_or_dev,
    CRED_PKGBASE_SET_KEYWORDS: trusted_user_or_dev,
    CRED_PKGBASE_DELETE: trusted_user_or_dev,
    CRED_PKGBASE_EDIT_COMAINTAINERS: trusted_user_or_dev,
    CRED_PKGBASE_DISOWN: trusted_user_or_dev,
    CRED_PKGBASE_LIST_VOTERS: trusted_user_or_dev,
    CRED_PKGBASE_UNFLAG: trusted_user_or_dev,
    CRED_PKGREQ_CLOSE: trusted_user_or_dev,
    CRED_PKGREQ_LIST: trusted_user_or_dev,
    CRED_TU_ADD_VOTE: trusted_user,
    CRED_TU_LIST_VOTES: trusted_user,
    CRED_TU_VOTE: trusted_user,
    CRED_ACCOUNT_EDIT_DEV: developer,
    CRED_PKGBASE_MERGE: trusted_user_or_dev,
}


def has_credential(user: User,
                   credential: int,
                   approved_users: list = tuple()):

    if user in approved_users:
        return True

    if credential in cred_filters:
        cred_filter = cred_filters.get(credential)
        return cred_filter(user)

    return False
