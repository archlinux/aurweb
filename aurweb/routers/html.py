""" AURWeb's primary routing module. Define all routes via @app.app.{get,post}
decorators in some way; more complex routes should be defined in their
own modules and imported here. """
import os

from datetime import datetime
from http import HTTPStatus

from fastapi import APIRouter, Form, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, generate_latest, multiprocess
from sqlalchemy import and_, case, or_

import aurweb.config
import aurweb.models.package_request

from aurweb import cookies, db, models, util
from aurweb.cache import db_count_cache
from aurweb.models.account_type import TRUSTED_USER_AND_DEV_ID, TRUSTED_USER_ID
from aurweb.models.package_request import PENDING_ID
from aurweb.packages.util import query_notified, query_voted, updated_packages
from aurweb.templates import make_context, render_template

router = APIRouter()


@router.get("/favicon.ico")
async def favicon(request: Request):
    """ Some browsers attempt to find a website's favicon via root uri at
    /favicon.ico, so provide a redirection here to our static icon. """
    return RedirectResponse("/static/images/favicon.ico")


@router.post("/language", response_class=RedirectResponse)
async def language(request: Request,
                   set_lang: str = Form(...),
                   next: str = Form(...),
                   q: str = Form(default=None)):
    """
    A POST route used to set a session's language.

    Return a 303 See Other redirect to {next}?next={next}. If we are
    setting the language on any page, we want to preserve query
    parameters across the redirect.
    """
    if next[0] != '/':
        return HTMLResponse(b"Invalid 'next' parameter.", status_code=400)

    query_string = "?" + q if q else str()

    # If the user is authenticated, update the user's LangPreference.
    if request.user.is_authenticated():
        with db.begin():
            request.user.LangPreference = set_lang

    # In any case, set the response's AURLANG cookie that never expires.
    response = RedirectResponse(url=f"{next}{query_string}",
                                status_code=HTTPStatus.SEE_OTHER)
    secure = aurweb.config.getboolean("options", "disable_http_login")
    response.set_cookie("AURLANG", set_lang,
                        secure=secure, httponly=secure,
                        samesite=cookies.samesite())
    return response


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """ Homepage route. """
    context = make_context(request, "Home")
    context['ssh_fingerprints'] = util.get_ssh_fingerprints()

    bases = db.query(models.PackageBase)

    redis = aurweb.redis.redis_connection()
    cache_expire = 300  # Five minutes.

    # Package statistics.
    query = bases.filter(models.PackageBase.PackagerUID.isnot(None))
    context["package_count"] = await db_count_cache(
        redis, "package_count", query, expire=cache_expire)

    query = bases.filter(
        and_(models.PackageBase.MaintainerUID.is_(None),
             models.PackageBase.PackagerUID.isnot(None))
    )
    context["orphan_count"] = await db_count_cache(
        redis, "orphan_count", query, expire=cache_expire)

    query = db.query(models.User)
    context["user_count"] = await db_count_cache(
        redis, "user_count", query, expire=cache_expire)

    query = query.filter(
        or_(models.User.AccountTypeID == TRUSTED_USER_ID,
            models.User.AccountTypeID == TRUSTED_USER_AND_DEV_ID))
    context["trusted_user_count"] = await db_count_cache(
        redis, "trusted_user_count", query, expire=cache_expire)

    # Current timestamp.
    now = int(datetime.utcnow().timestamp())

    seven_days = 86400 * 7  # Seven days worth of seconds.
    seven_days_ago = now - seven_days

    one_hour = 3600
    updated = bases.filter(
        and_(models.PackageBase.ModifiedTS - models.PackageBase.SubmittedTS >= one_hour,
             models.PackageBase.PackagerUID.isnot(None))
    )

    query = bases.filter(
        and_(models.PackageBase.SubmittedTS >= seven_days_ago,
             models.PackageBase.PackagerUID.isnot(None))
    )
    context["seven_days_old_added"] = await db_count_cache(
        redis, "seven_days_old_added", query, expire=cache_expire)

    query = updated.filter(models.PackageBase.ModifiedTS >= seven_days_ago)
    context["seven_days_old_updated"] = await db_count_cache(
        redis, "seven_days_old_updated", query, expire=cache_expire)

    year = seven_days * 52  # Fifty two weeks worth: one year.
    year_ago = now - year
    query = updated.filter(models.PackageBase.ModifiedTS >= year_ago)
    context["year_old_updated"] = await db_count_cache(
        redis, "year_old_updated", query, expire=cache_expire)

    query = bases.filter(
        models.PackageBase.ModifiedTS - models.PackageBase.SubmittedTS < 3600)
    context["never_updated"] = await db_count_cache(
        redis, "never_updated", query, expire=cache_expire)

    # Get the 15 most recently updated packages.
    context["package_updates"] = updated_packages(15, cache_expire)

    if request.user.is_authenticated():
        # Authenticated users get a few extra pieces of data for
        # the dashboard display.
        packages = db.query(models.Package).join(models.PackageBase)

        maintained = packages.join(
            models.User, models.PackageBase.MaintainerUID == models.User.ID
        ).filter(
            models.PackageBase.MaintainerUID == request.user.ID
        )

        # Packages maintained by the user that have been flagged.
        context["flagged_packages"] = maintained.filter(
            models.PackageBase.OutOfDateTS.isnot(None)
        ).order_by(
            models.PackageBase.ModifiedTS.desc(), models.Package.Name.asc()
        ).limit(50).all()

        # Flagged packages that request.user has voted for.
        context["flagged_packages_voted"] = query_voted(
            context.get("flagged_packages"), request.user)

        # Flagged packages that request.user is being notified about.
        context["flagged_packages_notified"] = query_notified(
            context.get("flagged_packages"), request.user)

        archive_time = aurweb.config.getint('options', 'request_archive_time')
        start = now - archive_time

        # Package requests created by request.user.
        context["package_requests"] = request.user.package_requests.filter(
            models.PackageRequest.RequestTS >= start
        ).order_by(
            # Order primarily by the Status column being PENDING_ID,
            # and secondarily by RequestTS; both in descending order.
            case([(models.PackageRequest.Status == PENDING_ID, 1)],
                 else_=0).desc(),
            models.PackageRequest.RequestTS.desc()
        ).limit(50).all()

        # Packages that the request user maintains or comaintains.
        context["packages"] = maintained.order_by(
            models.PackageBase.ModifiedTS.desc(), models.Package.Name.desc()
        ).limit(50).all()

        # Packages that request.user has voted for.
        context["packages_voted"] = query_voted(
            context.get("packages"), request.user)

        # Packages that request.user is being notified about.
        context["packages_notified"] = query_notified(
            context.get("packages"), request.user)

        # Any packages that the request user comaintains.
        context["comaintained"] = packages.join(
            models.PackageComaintainer
        ).filter(
            models.PackageComaintainer.UsersID == request.user.ID
        ).order_by(
            models.PackageBase.ModifiedTS.desc(), models.Package.Name.desc()
        ).limit(50).all()

        # Comaintained packages that request.user has voted for.
        context["comaintained_voted"] = query_voted(
            context.get("comaintained"), request.user)

        # Comaintained packages that request.user is being notified about.
        context["comaintained_notified"] = query_notified(
            context.get("comaintained"), request.user)

    return render_template(request, "index.html", context)


@router.get("/metrics")
async def metrics(request: Request):
    registry = CollectorRegistry()
    if os.environ.get("PROMETHEUS_MULTIPROC_DIR", None):  # pragma: no cover
        multiprocess.MultiProcessCollector(registry)
    data = generate_latest(registry)
    headers = {
        "Content-Type": CONTENT_TYPE_LATEST,
        "Content-Length": str(len(data))
    }
    return Response(data, headers=headers)


@router.get("/raisefivethree", response_class=HTMLResponse)
async def raise_service_unavailable(request: Request):
    raise HTTPException(status_code=HTTPStatus.SERVICE_UNAVAILABLE)
