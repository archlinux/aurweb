from datetime import datetime
from http import HTTPStatus

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

import aurweb.config

from aurweb import cookies
from aurweb.auth import auth_required
from aurweb.models import User
from aurweb.templates import make_variable_context, render_template

router = APIRouter()


async def login_template(request: Request, next: str, errors: list = None):
    """ Provide login-specific template context to render_template. """
    context = await make_variable_context(request, "Login", next)
    context["errors"] = errors
    context["url_base"] = f"{request.url.scheme}://{request.url.netloc}"
    return render_template(request, "login.html", context)


@router.get("/login", response_class=HTMLResponse)
@auth_required(False)
async def login_get(request: Request, next: str = "/"):
    return await login_template(request, next)


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
        return await login_template(request, next,
                                    errors=["Bad username or password."])

    cookie_timeout = cookies.timeout(remember_me)
    sid = user.login(request, passwd, cookie_timeout)
    if not sid:
        return await login_template(request, next,
                                    errors=["Bad username or password."])

    login_timeout = aurweb.config.getint("options", "login_timeout")

    expires_at = int(datetime.utcnow().timestamp()
                     + max(cookie_timeout, login_timeout))

    response = RedirectResponse(url=next,
                                status_code=HTTPStatus.SEE_OTHER)

    secure = aurweb.config.getboolean("options", "disable_http_login")
    response.set_cookie("AURSID", sid, expires=expires_at,
                        secure=secure, httponly=secure,
                        samesite=cookies.samesite())
    response.set_cookie("AURTZ", user.Timezone,
                        secure=secure, httponly=secure,
                        samesite=cookies.samesite())
    response.set_cookie("AURLANG", user.LangPreference,
                        secure=secure, httponly=secure,
                        samesite=cookies.samesite())
    return response


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
                                status_code=HTTPStatus.SEE_OTHER)
    response.delete_cookie("AURSID")
    response.delete_cookie("AURTZ")
    return response


@router.post("/logout")
@auth_required()
async def logout_post(request: Request, next: str = "/"):
    return await logout(request=request, next=next)
