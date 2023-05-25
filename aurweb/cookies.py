from fastapi import Request
from fastapi.responses import Response

from aurweb import config


def samesite() -> str:
    """Produce cookie SameSite value.

    Currently this is hard-coded to return "lax"

    :returns "lax"
    """
    return "lax"


def timeout(extended: bool) -> int:
    """Produce a session timeout based on `remember_me`.

    This method returns one of AUR_CONFIG's options.persistent_cookie_timeout
    and options.login_timeout based on the `extended` argument.

    The `extended` argument is typically the value of the AURREMEMBER
    cookie, defaulted to False.

    If `extended` is False, options.login_timeout is returned. Otherwise,
    if `extended` is True, options.persistent_cookie_timeout is returned.

    :param extended: Flag which generates an extended timeout when True
    :returns: Cookie timeout based on configuration options
    """
    timeout = config.getint("options", "login_timeout")
    if bool(extended):
        timeout = config.getint("options", "persistent_cookie_timeout")
    return timeout


def update_response_cookies(
    request: Request,
    response: Response,
    aursid: str = None,
) -> Response:
    """Update session cookies. This method is particularly useful
    when updating a cookie which was already set.

    The AURSID cookie's expiration is based on the AURREMEMBER cookie,
    which is retrieved from `request`.

    :param request: FastAPI request
    :param response: FastAPI response
    :param aursid: Optional AURSID cookie value
    :returns: Updated response
    """
    secure = config.getboolean("options", "disable_http_login")
    if aursid:
        remember_me = request.cookies.get("AURREMEMBER") == "True"
        response.set_cookie(
            "AURSID",
            aursid,
            secure=secure,
            httponly=secure,
            max_age=timeout(remember_me),
            samesite=samesite(),
        )
    return response
