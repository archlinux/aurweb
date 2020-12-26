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
