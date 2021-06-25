import asyncio
import http
import typing

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.middleware.sessions import SessionMiddleware

import aurweb.config
import aurweb.logging

from aurweb.auth import BasicAuthBackend
from aurweb.db import get_engine
from aurweb.routers import accounts, auth, errors, html, sso

# Setup the FastAPI app.
app = FastAPI(exception_handlers=errors.exceptions)


@app.on_event("startup")
async def app_startup():
    session_secret = aurweb.config.get("fastapi", "session_secret")
    if not session_secret:
        raise Exception("[fastapi] session_secret must not be empty")

    app.mount("/static/css",
              StaticFiles(directory="web/html/css"),
              name="static_css")
    app.mount("/static/js",
              StaticFiles(directory="web/html/js"),
              name="static_js")
    app.mount("/static/images",
              StaticFiles(directory="web/html/images"),
              name="static_images")

    # Add application middlewares.
    app.add_middleware(AuthenticationMiddleware, backend=BasicAuthBackend())
    app.add_middleware(SessionMiddleware, secret_key=session_secret)

    # Add application routes.
    app.include_router(sso.router)
    app.include_router(html.router)
    app.include_router(auth.router)
    app.include_router(accounts.router)

    # Initialize the database engine and ORM.
    get_engine()


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """
    Dirty HTML error page to replace the default JSON error responses.
    In the future this should use a proper Arch-themed HTML template.
    """
    phrase = http.HTTPStatus(exc.status_code).phrase
    return HTMLResponse(f"<h1>{exc.status_code} {phrase}</h1><p>{exc.detail}</p>",
                        status_code=exc.status_code)


@app.middleware("http")
async def add_security_headers(request: Request, call_next: typing.Callable):
    """ This middleware adds the CSP, XCTO, XFO and RP security
    headers to the HTTP response associated with request.

    CSP: Content-Security-Policy
    XCTO: X-Content-Type-Options
    RP: Referrer-Policy
    XFO: X-Frame-Options
    """
    response = asyncio.create_task(call_next(request))
    await asyncio.wait({response}, return_when=asyncio.FIRST_COMPLETED)
    response = response.result()

    # Add CSP header.
    nonce = request.user.nonce
    csp = "default-src 'self'; "
    script_hosts = [
        "ajax.googleapis.com",
        "cdn.jsdelivr.net"
    ]
    csp += f"script-src 'self' 'nonce-{nonce}' " + ' '.join(script_hosts)
    response.headers["Content-Security-Policy"] = csp

    # Add XTCO header.
    xcto = "nosniff"
    response.headers["X-Content-Type-Options"] = xcto

    # Add Referrer Policy header.
    rp = "same-origin"
    response.headers["Referrer-Policy"] = rp

    # Add X-Frame-Options header.
    xfo = "SAMEORIGIN"
    response.headers["X-Frame-Options"] = xfo

    return response
