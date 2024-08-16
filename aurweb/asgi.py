import hashlib
import http
import io
import os
import re
import sys
import traceback
import typing
from contextlib import asynccontextmanager
from urllib.parse import quote_plus

import requests
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import TemplateNotFound
from sqlalchemy import and_
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.middleware.sessions import SessionMiddleware

import aurweb.captcha  # noqa: F401
import aurweb.config
import aurweb.filters  # noqa: F401
from aurweb import aur_logging, prometheus, util
from aurweb.aur_redis import redis_connection
from aurweb.auth import BasicAuthBackend
from aurweb.db import get_engine, query
from aurweb.models import AcceptedTerm, Term
from aurweb.packages.util import get_pkg_or_base
from aurweb.prometheus import instrumentator
from aurweb.routers import APP_ROUTES
from aurweb.templates import make_context, render_template

logger = aur_logging.get_logger(__name__)
session_secret = aurweb.config.get("fastapi", "session_secret")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await app_startup()
    yield


# Setup the FastAPI app.
app = FastAPI(lifespan=lifespan)


# Instrument routes with the prometheus-fastapi-instrumentator
# library with custom collectors and expose /metrics.
instrumentator().add(prometheus.http_api_requests_total())
instrumentator().add(prometheus.http_requests_total())
instrumentator().instrument(app)


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
    recursion_limit = int(
        os.environ.get("TEST_RECURSION_LIMIT", sys.getrecursionlimit() + 1000)
    )
    sys.setrecursionlimit(recursion_limit)

    backend = aurweb.config.get("database", "backend")
    if backend not in aurweb.db.DRIVERS:
        raise ValueError(
            f"The configured database backend ({backend}) is unsupported. "
            f"Supported backends: {str(aurweb.db.DRIVERS.keys())}"
        )

    if not session_secret:
        raise Exception("[fastapi] session_secret must not be empty")

    if not os.environ.get("PROMETHEUS_MULTIPROC_DIR", None):
        logger.warning(
            "$PROMETHEUS_MULTIPROC_DIR is not set, the /metrics "
            "endpoint is disabled."
        )

    app.mount("/static", StaticFiles(directory="static"), name="static_files")

    # Add application routes.
    def add_router(module):
        app.include_router(module.router)

    util.apply_all(APP_ROUTES, add_router)

    # Initialize the database engine and ORM.
    get_engine()


async def internal_server_error(request: Request, exc: Exception) -> Response:
    """
    Catch all uncaught Exceptions thrown in a route.

    :param request: FastAPI Request
    :return: Rendered 500.html template with status_code 500
    """
    repo = aurweb.config.get("notifications", "gitlab-instance")
    project = aurweb.config.get("notifications", "error-project")
    token = aurweb.config.get("notifications", "error-token")

    context = make_context(request, "Internal Server Error")

    # Print out the exception via `traceback` and store the value
    # into the `traceback` context variable.
    tb_io = io.StringIO()
    traceback.print_exc(file=tb_io)
    tb = tb_io.getvalue()
    context["traceback"] = tb

    # Produce a SHA1 hash of the traceback string.
    tb_hash = hashlib.sha1(tb.encode()).hexdigest()
    tb_id = tb_hash[:7]

    redis = redis_connection()
    key = f"tb:{tb_hash}"
    retval = redis.get(key)
    if not retval:
        # Expire in one hour; this is just done to make sure we
        # don't infinitely store these values, but reduce the number
        # of automated reports (notification below). At this time of
        # writing, unexpected exceptions are not common, thus this
        # will not produce a large memory footprint in redis.
        pipe = redis.pipeline()
        pipe.set(key, tb)
        pipe.expire(key, 86400)  # One day.
        pipe.execute()

        # Send out notification about it.
        if "set-me" not in (project, token):
            proj = quote_plus(project)
            endp = f"{repo}/api/v4/projects/{proj}/issues"

            base = f"{request.url.scheme}://{request.url.netloc}"
            title = f"Traceback [{tb_id}]: {base}{request.url.path}"
            desc = [
                "DISCLAIMER",
                "----------",
                "**This issue is confidential** and should be sanitized "
                "before sharing with users or developers. Please ensure "
                "you've completed the following tasks:",
                "- [ ] I have removed any sensitive data and "
                "the description history.",
                "",
                "Exception Details",
                "-----------------",
                f"- Route: `{request.url.path}`",
                f"- User: `{request.user.Username}`",
                f"- Email: `{request.user.Email}`",
            ]

            # Add method-specific information to the description.
            if request.method.lower() == "get":
                # get
                if request.url.query:
                    desc = desc + [f"- Query: `{request.url.query}`"]
                desc += ["", f"```{tb}```"]
            else:
                # post
                form_data = str(dict(request.state.form_data))
                desc = desc + [f"- Data: `{form_data}`"] + ["", f"```{tb}```"]

            headers = {"Authorization": f"Bearer {token}"}
            data = {
                "title": title,
                "description": "\n".join(desc),
                "labels": ["triage"],
                "confidential": True,
            }
            logger.info(endp)
            resp = requests.post(endp, json=data, headers=headers)
            if resp.status_code != http.HTTPStatus.CREATED:
                logger.error(f"Unable to report exception to {repo}: {resp.text}")
        else:
            logger.warning(
                "Unable to report an exception found due to "
                "unset notifications.error-{{project,token}}"
            )

        # Log details about the exception traceback.
        logger.error(f"FATAL[{tb_id}]: An unexpected exception has occurred.")
        logger.error(tb)
    else:
        retval = retval.decode()

    return render_template(
        request,
        "errors/500.html",
        context,
        status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR,
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> Response:
    """Handle an HTTPException thrown in a route."""
    phrase = http.HTTPStatus(exc.status_code).phrase
    context = make_context(request, phrase)
    context["exc"] = exc
    context["phrase"] = phrase

    # Additional context for some exceptions.
    if exc.status_code == http.HTTPStatus.NOT_FOUND:
        tokens = request.url.path.split("/")
        matches = re.match("^([a-z0-9][a-z0-9.+_-]*?)(\\.git)?$", tokens[1])
        if matches and len(tokens) == 2:
            try:
                pkgbase = get_pkg_or_base(matches.group(1))
                context["pkgbase"] = pkgbase
                context["git_clone_uri_anon"] = aurweb.config.get("options", "git_clone_uri_anon")
                context["git_clone_uri_priv"] = aurweb.config.get("options", "git_clone_uri_priv")
            except HTTPException:
                pass

    try:
        return render_template(
            request, f"errors/{exc.status_code}.html", context, exc.status_code
        )
    except TemplateNotFound:
        return render_template(request, "errors/detail.html", context, exc.status_code)


@app.middleware("http")
async def add_security_headers(request: Request, call_next: typing.Callable):
    """This middleware adds the CSP, XCTO, XFO and RP security
    headers to the HTTP response associated with request.

    CSP: Content-Security-Policy
    XCTO: X-Content-Type-Options
    RP: Referrer-Policy
    XFO: X-Frame-Options
    """
    try:
        response = await util.error_or_result(call_next, request)
    except Exception as exc:
        return await internal_server_error(request, exc)

    # Add CSP header.
    nonce = request.user.nonce
    csp = "default-src 'self'; "

    # swagger-ui needs access to cdn.jsdelivr.net javascript
    script_hosts = ["cdn.jsdelivr.net"]
    csp += f"script-src 'self' 'unsafe-inline' 'nonce-{nonce}' " + " ".join(
        script_hosts
    )

    # swagger-ui needs access to cdn.jsdelivr.net css
    css_hosts = ["cdn.jsdelivr.net"]
    csp += "; style-src 'self' 'unsafe-inline' " + " ".join(css_hosts)
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
    """This middleware function redirects authenticated users if they
    have any outstanding Terms to agree to."""
    if request.user.is_authenticated() and request.url.path != "/tos":
        accepted = (
            query(Term)
            .join(AcceptedTerm)
            .filter(
                and_(
                    AcceptedTerm.UsersID == request.user.ID,
                    AcceptedTerm.TermsID == Term.ID,
                    AcceptedTerm.Revision >= Term.Revision,
                ),
            )
        )
        if query(Term).count() - accepted.count() > 0:
            return RedirectResponse("/tos", status_code=int(http.HTTPStatus.SEE_OTHER))

    return await util.error_or_result(call_next, request)


@app.middleware("http")
async def id_redirect_middleware(request: Request, call_next: typing.Callable):
    id = request.query_params.get("id")

    if id is not None:
        # Preserve query string.
        qs = []
        for k, v in request.query_params.items():
            if k != "id":
                qs.append(f"{k}={quote_plus(str(v))}")
        qs = str() if not qs else "?" + "&".join(qs)

        path = request.url.path.rstrip("/")
        return RedirectResponse(f"{path}/{id}{qs}")

    return await util.error_or_result(call_next, request)


# Add application middlewares.
app.add_middleware(AuthenticationMiddleware, backend=BasicAuthBackend())
app.add_middleware(SessionMiddleware, secret_key=session_secret)
