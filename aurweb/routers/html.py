""" AURWeb's primary routing module. Define all routes via @app.app.{get,post}
decorators in some way; more complex routes should be defined in their
own modules and imported here. """
import os
from http import HTTPStatus

from fastapi import APIRouter, Form, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    generate_latest,
    multiprocess,
)
from sqlalchemy import case, or_

import aurweb.config
import aurweb.models.package_request
from aurweb import aur_logging, cookies, db, models, statistics, time, util
from aurweb.exceptions import handle_form_exceptions
from aurweb.models.package_request import PENDING_ID
from aurweb.packages.util import query_notified, query_voted, updated_packages
from aurweb.templates import make_context, render_template

logger = aur_logging.get_logger(__name__)
router = APIRouter()


@router.get("/favicon.ico")
async def favicon(request: Request):
    """Some browsers attempt to find a website's favicon via root uri at
    /favicon.ico, so provide a redirection here to our static icon."""
    return RedirectResponse("/static/images/favicon.ico")


@db.async_retry_deadlock
@router.post("/language", response_class=RedirectResponse)
@handle_form_exceptions
async def language(
    request: Request,
    set_lang: str = Form(...),
    next: str = Form(...),
    q: str = Form(default=None),
):
    """
    A POST route used to set a session's language.

    Return a 303 See Other redirect to {next}?next={next}. If we are
    setting the language on any page, we want to preserve query
    parameters across the redirect.
    """
    if next[0] != "/":
        return HTMLResponse(b"Invalid 'next' parameter.", status_code=400)

    query_string = "?" + q if q else str()

    response = RedirectResponse(
        url=f"{next}{query_string}", status_code=HTTPStatus.SEE_OTHER
    )

    # If the user is authenticated, update the user's LangPreference.
    # Otherwise set an AURLANG cookie
    if request.user.is_authenticated():
        with db.begin():
            request.user.LangPreference = set_lang
    else:
        secure = aurweb.config.getboolean("options", "disable_http_login")
        perma_timeout = aurweb.config.getint("options", "permanent_cookie_timeout")

        response.set_cookie(
            "AURLANG",
            set_lang,
            secure=secure,
            httponly=secure,
            max_age=perma_timeout,
            samesite=cookies.samesite(),
        )

    return response


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Homepage route."""
    context = make_context(request, "Home")
    context["ssh_fingerprints"] = util.get_ssh_fingerprints()

    cache_expire = aurweb.config.getint("cache", "expiry_time_statistics", 300)

    # Package statistics.
    counts = statistics.get_homepage_counts()
    for k in counts:
        context[k] = counts[k]

    # Get the 15 most recently updated packages.
    context["package_updates"] = updated_packages(15, cache_expire)

    if request.user.is_authenticated():
        # Authenticated users get a few extra pieces of data for
        # the dashboard display.
        packages = db.query(models.Package).join(models.PackageBase)

        maintained = (
            packages.join(
                models.PackageComaintainer,
                models.PackageComaintainer.PackageBaseID == models.PackageBase.ID,
                isouter=True,
            )
            .join(
                models.User,
                or_(
                    models.PackageBase.MaintainerUID == models.User.ID,
                    models.PackageComaintainer.UsersID == models.User.ID,
                ),
            )
            .filter(models.User.ID == request.user.ID)
        )

        # Packages maintained by the user that have been flagged.
        context["flagged_packages"] = (
            maintained.filter(models.PackageBase.OutOfDateTS.isnot(None))
            .order_by(models.PackageBase.ModifiedTS.desc(), models.Package.Name.asc())
            .limit(50)
            .all()
        )

        # Flagged packages that request.user has voted for.
        context["flagged_packages_voted"] = query_voted(
            context.get("flagged_packages"), request.user
        )

        # Flagged packages that request.user is being notified about.
        context["flagged_packages_notified"] = query_notified(
            context.get("flagged_packages"), request.user
        )

        archive_time = aurweb.config.getint("options", "request_archive_time")
        start = time.utcnow() - archive_time

        # Package requests created by request.user.
        context["package_requests"] = (
            request.user.package_requests.filter(
                models.PackageRequest.RequestTS >= start
            )
            .order_by(
                # Order primarily by the Status column being PENDING_ID,
                # and secondarily by RequestTS; both in descending order.
                case((models.PackageRequest.Status == PENDING_ID, 1), else_=0).desc(),
                models.PackageRequest.RequestTS.desc(),
            )
            .limit(50)
            .all()
        )

        # Packages that the request user maintains or comaintains.
        context["packages"] = (
            maintained.filter(models.User.ID == models.PackageBase.MaintainerUID)
            .order_by(models.PackageBase.ModifiedTS.desc(), models.Package.Name.desc())
            .limit(50)
            .all()
        )

        # Packages that request.user has voted for.
        context["packages_voted"] = query_voted(context.get("packages"), request.user)

        # Packages that request.user is being notified about.
        context["packages_notified"] = query_notified(
            context.get("packages"), request.user
        )

        # Any packages that the request user comaintains.
        context["comaintained"] = (
            packages.join(models.PackageComaintainer)
            .filter(models.PackageComaintainer.UsersID == request.user.ID)
            .order_by(models.PackageBase.ModifiedTS.desc(), models.Package.Name.desc())
            .limit(50)
            .all()
        )

        # Comaintained packages that request.user has voted for.
        context["comaintained_voted"] = query_voted(
            context.get("comaintained"), request.user
        )

        # Comaintained packages that request.user is being notified about.
        context["comaintained_notified"] = query_notified(
            context.get("comaintained"), request.user
        )

    return render_template(request, "index.html", context)


@router.get("/{archive}.sha256")
async def archive_sha256(request: Request, archive: str):
    archivedir = aurweb.config.get("mkpkglists", "archivedir")
    hashfile = os.path.join(archivedir, f"{archive}.sha256")
    if not os.path.exists(hashfile):
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND)

    with open(hashfile) as f:
        hash_value = f.read()
    headers = {"Content-Type": "text/plain"}
    return Response(hash_value, headers=headers)


@router.get("/metrics")
async def metrics(request: Request):
    if not os.environ.get("PROMETHEUS_MULTIPROC_DIR", None):
        return Response(
            "Prometheus metrics are not enabled.",
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
        )

    # update prometheus gauges for packages and users
    statistics.update_prometheus_metrics()

    registry = CollectorRegistry()
    multiprocess.MultiProcessCollector(registry)
    data = generate_latest(registry)
    headers = {"Content-Type": CONTENT_TYPE_LATEST, "Content-Length": str(len(data))}
    return Response(data, headers=headers)


@router.get("/raisefivethree", response_class=HTMLResponse)
async def raise_service_unavailable(request: Request):
    raise HTTPException(status_code=HTTPStatus.SERVICE_UNAVAILABLE)
