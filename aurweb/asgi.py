import asyncio
import http
import os
import sys
import typing

from urllib.parse import quote_plus

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from prometheus_client import multiprocess
from sqlalchemy import and_, or_
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.middleware.sessions import SessionMiddleware

import aurweb.config
import aurweb.logging

from aurweb.auth import BasicAuthBackend
from aurweb.db import get_engine, query
from aurweb.models import AcceptedTerm, Term
from aurweb.prometheus import http_api_requests_total, http_requests_total, instrumentator
from aurweb.routers import accounts, auth, errors, html, packages, rpc, rss, sso, trusted_user

# Setup the FastAPI app.
app = FastAPI(exception_handlers=errors.exceptions)

# Instrument routes with the prometheus-fastapi-instrumentator
# library with custom collectors and expose /metrics.
instrumentator().add(http_api_requests_total())
instrumentator().add(http_requests_total())
instrumentator().instrument(app)


@app.on_event("startup")
async def app_startup():
    # https://stackoverflow.com/questions/67054759/about-the-maximum-recursion-error-in-fastapi
    # Test failures have been observed by internal starlette code when
    # using starlette.testclient.TestClient. Looking around in regards
    # to the recursion error has really not recommended a course of action
    # other than increasing the recursion limit. For now, that is how
    # we handle the issue: an optional TEST_RECURSION_LIMIT env var
    # provided by the user. Docker uses .env's TEST_RECURSION_LIMIT
    # when running test suites.
    # TODO: Find a proper fix to this issue.
    recursion_limit = int(os.environ.get(
        "TEST_RECURSION_LIMIT", sys.getrecursionlimit()))
    sys.setrecursionlimit(recursion_limit)

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
    app.include_router(trusted_user.router)
    app.include_router(rss.router)
    app.include_router(packages.router)
    app.include_router(rpc.router)

    # Initialize the database engine and ORM.
    get_engine()


def child_exit(server, worker):  # pragma: no cover
    """ This function is required for gunicorn customization
    of prometheus multiprocessing. """
    multiprocess.mark_process_dead(worker.pid)


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
    script_hosts = []
    csp += f"script-src 'self' 'nonce-{nonce}' " + ' '.join(script_hosts)
    # It's fine if css is inlined.
    csp += "; style-src 'self' 'unsafe-inline'"
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


@app.middleware("http")
async def check_terms_of_service(request: Request, call_next: typing.Callable):
    """ This middleware function redirects authenticated users if they
    have any outstanding Terms to agree to. """
    if request.user.is_authenticated() and request.url.path != "/tos":
        unaccepted = query(Term).join(AcceptedTerm).filter(
            or_(AcceptedTerm.UsersID != request.user.ID,
                and_(AcceptedTerm.UsersID == request.user.ID,
                     AcceptedTerm.TermsID == Term.ID,
                     AcceptedTerm.Revision < Term.Revision)))
        if query(Term).count() > unaccepted.count():
            return RedirectResponse(
                "/tos", status_code=int(http.HTTPStatus.SEE_OTHER))

    task = asyncio.create_task(call_next(request))
    await asyncio.wait({task}, return_when=asyncio.FIRST_COMPLETED)
    return task.result()


@app.middleware("http")
async def id_redirect_middleware(request: Request, call_next: typing.Callable):
    id = request.query_params.get("id")

    if id is not None:
        # Preserve query string.
        qs = []
        for k, v in request.query_params.items():
            if k != "id":
                qs.append(f"{k}={quote_plus(str(v))}")
        qs = str() if not qs else '?' + '&'.join(qs)

        path = request.url.path.rstrip('/')
        return RedirectResponse(f"{path}/{id}{qs}")

    task = asyncio.create_task(call_next(request))
    await asyncio.wait({task}, return_when=asyncio.FIRST_COMPLETED)
    return task.result()
