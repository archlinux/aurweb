""" AURWeb's primary routing module. Define all routes via @app.app.{get,post}
decorators in some way; more complex routes should be defined in their
own modules and imported here. """
from datetime import datetime
from http import HTTPStatus

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import and_, or_

import aurweb.config
import aurweb.models.package_request

from aurweb import db, util
from aurweb.cache import db_count_cache
from aurweb.models.account_type import TRUSTED_USER_AND_DEV_ID, TRUSTED_USER_ID
from aurweb.models.package import Package
from aurweb.models.package_base import PackageBase
from aurweb.models.package_comaintainer import PackageComaintainer
from aurweb.models.package_request import PackageRequest
from aurweb.models.user import User
from aurweb.packages.util import updated_packages
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
    from aurweb.db import session

    if next[0] != '/':
        return HTMLResponse(b"Invalid 'next' parameter.", status_code=400)

    query_string = "?" + q if q else str()

    # If the user is authenticated, update the user's LangPreference.
    if request.user.is_authenticated():
        request.user.LangPreference = set_lang
        session.commit()

    # In any case, set the response's AURLANG cookie that never expires.
    response = RedirectResponse(url=f"{next}{query_string}",
                                status_code=int(HTTPStatus.SEE_OTHER))
    secure_cookies = aurweb.config.getboolean("options", "disable_http_login")
    response.set_cookie("AURLANG", set_lang,
                        secure=secure_cookies, httponly=True)
    return util.add_samesite_fields(response, "strict")


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """ Homepage route. """
    context = make_context(request, "Home")
    context['ssh_fingerprints'] = util.get_ssh_fingerprints()

    bases = db.query(PackageBase)

    redis = aurweb.redis.redis_connection()
    stats_expire = 300  # Five minutes.
    updates_expire = 600  # Ten minutes.

    # Package statistics.
    query = bases.filter(PackageBase.PackagerUID.isnot(None))
    context["package_count"] = await db_count_cache(
        redis, "package_count", query, expire=stats_expire)

    query = bases.filter(
        and_(PackageBase.MaintainerUID.is_(None),
             PackageBase.PackagerUID.isnot(None))
    )
    context["orphan_count"] = await db_count_cache(
        redis, "orphan_count", query, expire=stats_expire)

    query = db.query(User)
    context["user_count"] = await db_count_cache(
        redis, "user_count", query, expire=stats_expire)

    query = query.filter(
        or_(User.AccountTypeID == TRUSTED_USER_ID,
            User.AccountTypeID == TRUSTED_USER_AND_DEV_ID))
    context["trusted_user_count"] = await db_count_cache(
        redis, "trusted_user_count", query, expire=stats_expire)

    # Current timestamp.
    now = int(datetime.utcnow().timestamp())

    seven_days = 86400 * 7  # Seven days worth of seconds.
    seven_days_ago = now - seven_days

    one_hour = 3600
    updated = bases.filter(
        and_(PackageBase.ModifiedTS - PackageBase.SubmittedTS >= one_hour,
             PackageBase.PackagerUID.isnot(None))
    )

    query = bases.filter(
        and_(PackageBase.SubmittedTS >= seven_days_ago,
             PackageBase.PackagerUID.isnot(None))
    )
    context["seven_days_old_added"] = await db_count_cache(
        redis, "seven_days_old_added", query, expire=stats_expire)

    query = updated.filter(PackageBase.ModifiedTS >= seven_days_ago)
    context["seven_days_old_updated"] = await db_count_cache(
        redis, "seven_days_old_updated", query, expire=stats_expire)

    year = seven_days * 52  # Fifty two weeks worth: one year.
    year_ago = now - year
    query = updated.filter(PackageBase.ModifiedTS >= year_ago)
    context["year_old_updated"] = await db_count_cache(
        redis, "year_old_updated", query, expire=stats_expire)

    query = bases.filter(
        PackageBase.ModifiedTS - PackageBase.SubmittedTS < 3600)
    context["never_updated"] = await db_count_cache(
        redis, "never_updated", query, expire=stats_expire)

    # Get the 15 most recently updated packages.
    context["package_updates"] = updated_packages(15, updates_expire)

    if request.user.is_authenticated():
        # Authenticated users get a few extra pieces of data for
        # the dashboard display.
        packages = db.query(Package).join(PackageBase)

        maintained = packages.join(
            User, PackageBase.MaintainerUID == User.ID
        ).filter(
            PackageBase.MaintainerUID == request.user.ID
        )

        context["flagged_packages"] = maintained.filter(
            PackageBase.OutOfDateTS.isnot(None)
        ).order_by(
            PackageBase.ModifiedTS.desc(), Package.Name.asc()
        ).limit(50).all()

        archive_time = aurweb.config.getint('options', 'request_archive_time')
        start = now - archive_time
        context["package_requests"] = request.user.package_requests.filter(
            PackageRequest.RequestTS >= start
        ).limit(50).all()

        # Packages that the request user maintains or comaintains.
        context["packages"] = maintained.order_by(
            PackageBase.ModifiedTS.desc(), Package.Name.desc()
        ).limit(50).all()

        # Any packages that the request user comaintains.
        context["comaintained"] = packages.join(
            PackageComaintainer).filter(
            PackageComaintainer.UsersID == request.user.ID).order_by(
            PackageBase.ModifiedTS.desc(), Package.Name.desc()
        ).limit(50).all()

    return render_template(request, "index.html", context)


# A route that returns a error 503. For testing purposes.
@router.get("/raisefivethree", response_class=HTMLResponse)
async def raise_service_unavailable(request: Request):
    raise HTTPException(status_code=503)
