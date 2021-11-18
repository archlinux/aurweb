import functools

from datetime import datetime
from http import HTTPStatus

import fastapi

from fastapi.responses import RedirectResponse
from sqlalchemy import and_
from starlette.authentication import AuthCredentials, AuthenticationBackend
from starlette.requests import HTTPConnection

import aurweb.config

from aurweb import db, l10n, util
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
        sid = conn.cookies.get("AURSID")
        if not sid:
            return (None, AnonymousUser())

        now_ts = datetime.utcnow().timestamp()
        record = db.query(Session).filter(
            and_(Session.SessionID == sid,
                 Session.LastUpdateTS >= now_ts)).first()

        # If no session with sid and a LastUpdateTS now or later exists.
        if not record:
            return (None, AnonymousUser())

        # At this point, we cannot have an invalid user if the record
        # exists, due to ForeignKey constraints in the schema upheld
        # by mysqlclient.
        user = db.query(User).filter(User.ID == record.UsersID).first()
        user.nonce = util.make_nonce()
        user.authenticated = True

        return (AuthCredentials(["authenticated"]), user)


def auth_required(is_required: bool = True,
                  template: tuple = None,
                  status_code: HTTPStatus = HTTPStatus.UNAUTHORIZED):
    """ Authentication route decorator.

    If template is given, it will be rendered with Unauthorized if
    is_required does not match.

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

                if is_required:
                    if request.method == "GET":
                        url = request.url.path
                    elif request.method == "POST" and (referer := request.headers.get("Referer")):
                        aur = aurweb.config.get("options", "aur_location") + "/"
                        if not referer.startswith(aur):
                            raise HTTPException(status_code=HTTPStatus.BAD_REQUEST,
                                                detail=_("Bad Referer header."))
                        url = referer[len(aur) - 1:]

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
            if request.user.AccountTypeID not in one_of:
                return RedirectResponse("/",
                                        status_code=int(HTTPStatus.SEE_OTHER))
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator
