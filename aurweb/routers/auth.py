from datetime import datetime
from http import HTTPStatus

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

import aurweb.config

from aurweb import util
from aurweb.auth import auth_required
from aurweb.models.user import User
from aurweb.templates import make_context, render_template

router = APIRouter()


def login_template(request: Request, next: str, errors: list = None):
    """ Provide login-specific template context to render_template. """
    context = make_context(request, "Login", next)
    context["errors"] = errors
    context["url_base"] = f"{request.url.scheme}://{request.url.netloc}"
    return render_template(request, "login.html", context)


@router.get("/login", response_class=HTMLResponse)
@auth_required(False)
async def login_get(request: Request, next: str = "/"):
    return login_template(request, next)


@router.post("/login", response_class=HTMLResponse)
@auth_required(False)
async def login_post(request: Request,
                     next: str = Form(...),
                     user: str = Form(default=str()),
                     passwd: str = Form(default=str()),
                     remember_me: bool = Form(default=False)):
    from aurweb.db import session

    user = session.query(User).filter(User.Username == user).first()
    if not user:
        return login_template(request, next,
                              errors=["Bad username or password."])

    cookie_timeout = 0

    if remember_me:
        cookie_timeout = aurweb.config.getint(
            "options", "persistent_cookie_timeout")

    sid = user.login(request, passwd, cookie_timeout)
    if not sid:
        return login_template(request, next,
                              errors=["Bad username or password."])

    login_timeout = aurweb.config.getint("options", "login_timeout")

    expires_at = int(datetime.utcnow().timestamp()
                     + max(cookie_timeout, login_timeout))

    response = RedirectResponse(url=next,
                                status_code=int(HTTPStatus.SEE_OTHER))

    secure_cookies = aurweb.config.getboolean("options", "disable_http_login")
    response.set_cookie("AURSID", sid, expires=expires_at,
                        secure=secure_cookies, httponly=True)
    response.set_cookie("AURTZ", user.Timezone,
                        secure=secure_cookies, httponly=True)
    response.set_cookie("AURLANG", user.LangPreference,
                        secure=secure_cookies, httponly=True)
    return util.add_samesite_fields(response, "strict")


@router.get("/logout")
@auth_required()
async def logout(request: Request, next: str = "/"):
    """ A GET and POST route for logging out.

    @param request FastAPI request
    @param next Route to redirect to
    """
    if request.user.is_authenticated():
        request.user.logout(request)

    # Use 303 since we may be handling a post request, that'll get it
    # to redirect to a get request.
    response = RedirectResponse(url=next,
                                status_code=int(HTTPStatus.SEE_OTHER))
    response.delete_cookie("AURSID")
    response.delete_cookie("AURTZ")
    return response


@router.post("/logout")
@auth_required()
async def logout_post(request: Request, next: str = "/"):
    return await logout(request=request, next=next)
