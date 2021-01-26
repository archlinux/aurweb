import functools

from datetime import datetime
from http import HTTPStatus

from fastapi.responses import RedirectResponse
from starlette.authentication import AuthCredentials, AuthenticationBackend, AuthenticationError
from starlette.requests import HTTPConnection

from aurweb.models.session import Session
from aurweb.models.user import User
from aurweb.templates import make_context, render_template


class AnonymousUser:
    @staticmethod
    def is_authenticated():
        return False

    @staticmethod
    def has_credential(credential):
        return False


class BasicAuthBackend(AuthenticationBackend):
    async def authenticate(self, conn: HTTPConnection):
        from aurweb.db import session

        sid = conn.cookies.get("AURSID")
        if not sid:
            return None, AnonymousUser()

        now_ts = datetime.utcnow().timestamp()
        record = session.query(Session).filter(
            Session.SessionID == sid, Session.LastUpdateTS >= now_ts).first()
        if not record:
            return None, AnonymousUser()

        user = session.query(User).filter(User.ID == record.UsersID).first()
        if not user:
            raise AuthenticationError(f"Invalid User ID: {record.UsersID}")

        user.authenticated = True
        return AuthCredentials(["authenticated"]), user


def auth_required(is_required: bool = True,
                  redirect: str = "/",
                  template: tuple = None):
    """ Authentication route decorator.

    If redirect is given, the user will be redirected if the auth state
    does not match is_required.

    If template is given, it will be rendered with Unauthorized if
    is_required does not match and take priority over redirect.

    :param is_required: A boolean indicating whether the function requires auth
    :param redirect: Path to redirect to if is_required isn't True
    :param template: A template tuple: ("template.html", "Template Page")
    """

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(request, *args, **kwargs):
            if request.user.is_authenticated() != is_required:
                status_code = int(HTTPStatus.UNAUTHORIZED)
                url = "/"
                if redirect:
                    status_code = int(HTTPStatus.SEE_OTHER)
                    url = redirect
                if template:
                    path, title = template
                    context = make_context(request, title)
                    return render_template(request, path, context,
                                           status_code=int(HTTPStatus.UNAUTHORIZED))
                return RedirectResponse(url=url, status_code=status_code)
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


def has_any(user, *account_types):
    return str(user.AccountType) in set(account_types)


def user_developer_or_trusted_user(user):
    return has_any(user, "User", "Trusted User", "Developer",
                   "Trusted User & Developer")


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
