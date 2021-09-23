from http import HTTPStatus
from typing import Any, Dict

from fastapi import APIRouter, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy import and_

import aurweb.filters
import aurweb.models.package_comment
import aurweb.models.package_keyword
import aurweb.packages.util

from aurweb import db
from aurweb.models.license import License
from aurweb.models.package import Package
from aurweb.models.package_base import PackageBase
from aurweb.models.package_dependency import PackageDependency
from aurweb.models.package_license import PackageLicense
from aurweb.models.package_notification import PackageNotification
from aurweb.models.package_relation import PackageRelation
from aurweb.models.package_request import PackageRequest
from aurweb.models.package_source import PackageSource
from aurweb.models.package_vote import PackageVote
from aurweb.models.relation_type import CONFLICTS_ID
from aurweb.packages.search import PackageSearch
from aurweb.packages.util import get_pkgbase, query_notified, query_voted
from aurweb.templates import make_context, render_template

router = APIRouter()


async def packages_get(request: Request, context: Dict[str, Any]):
    # Query parameters used in this request.
    context["q"] = dict(request.query_params)

    # Per page and offset.
    per_page = context["PP"] = int(request.query_params.get("PP", 50))
    offset = context["O"] = int(request.query_params.get("O", 0))

    # Query search by.
    search_by = context["SeB"] = request.query_params.get("SeB", "nd")

    # Query sort by.
    sort_by = context["SB"] = request.query_params.get("SB", "n")

    # Query sort order.
    sort_order = request.query_params.get("SO", None)

    # Apply ordering, limit and offset.
    search = PackageSearch(request.user)

    # For each keyword found in K, apply a search_by filter.
    # This means that for any sentences separated by spaces,
    # they are used as if they were ANDed.
    keywords = context["K"] = request.query_params.get("K", str())
    keywords = keywords.split(" ")
    for keyword in keywords:
        search.search_by(search_by, keyword)

    flagged = request.query_params.get("outdated", None)
    if flagged:
        # If outdated was given, set it up in the context.
        context["outdated"] = flagged

        # When outdated is set to "on," we filter records which do have
        # an OutOfDateTS. When it's set to "off," we filter out any which
        # do **not** have OutOfDateTS.
        criteria = None
        if flagged == "on":
            criteria = PackageBase.OutOfDateTS.isnot
        else:
            criteria = PackageBase.OutOfDateTS.is_

        # Apply the flag criteria to our PackageSearch.query.
        search.query = search.query.filter(criteria(None))

    submit = request.query_params.get("submit", "Go")
    if submit == "Orphans":
        # If the user clicked the "Orphans" button, we only want
        # orphaned packages.
        search.query = search.query.filter(PackageBase.MaintainerUID.is_(None))

    # Apply user-specified specified sort column and ordering.
    search.sort_by(sort_by, sort_order)

    # If no SO was given, default the context SO to 'a' (Ascending).
    # By default, if no SO is given, the search should sort by 'd'
    # (Descending), but display "Ascending" for the Sort order select.
    if sort_order is None:
        sort_order = "a"
    context["SO"] = sort_order

    # Insert search results into the context.
    results = search.results()
    context["packages"] = results.limit(per_page).offset(offset)
    context["packages_voted"] = query_voted(
        context.get("packages"), request.user)
    context["packages_notified"] = query_notified(
        context.get("packages"), request.user)
    context["packages_count"] = search.total_count

    return render_template(request, "packages.html", context)


@router.get("/packages")
async def packages(request: Request) -> Response:
    context = make_context(request, "Packages")
    return await packages_get(request, context)


async def make_single_context(request: Request,
                              pkgbase: PackageBase) -> Dict[str, Any]:
    """ Make a basic context for package or pkgbase.

    :param request: FastAPI request
    :param pkgbase: PackageBase instance
    :return: A pkgbase context without specific differences
    """
    context = make_context(request, pkgbase.Name)
    context["git_clone_uri_anon"] = aurweb.config.get("options",
                                                      "git_clone_uri_anon")
    context["git_clone_uri_priv"] = aurweb.config.get("options",
                                                      "git_clone_uri_priv")
    context["pkgbase"] = pkgbase
    context["packages_count"] = pkgbase.packages.count()
    context["keywords"] = pkgbase.keywords
    context["comments"] = pkgbase.comments
    context["is_maintainer"] = (request.user.is_authenticated()
                                and request.user.ID == pkgbase.MaintainerUID)
    context["notified"] = request.user.package_notifications.filter(
        PackageNotification.PackageBaseID == pkgbase.ID
    ).scalar()

    context["out_of_date"] = bool(pkgbase.OutOfDateTS)

    context["voted"] = request.user.package_votes.filter(
        PackageVote.PackageBaseID == pkgbase.ID).scalar()

    context["requests"] = pkgbase.requests.filter(
        PackageRequest.ClosedTS.is_(None)
    ).count()

    return context


@router.get("/packages/{name}")
async def package(request: Request, name: str) -> Response:
    # Get the PackageBase.
    pkgbase = get_pkgbase(name)

    # Add our base information.
    context = await make_single_context(request, pkgbase)

    # Package sources.
    context["sources"] = db.query(PackageSource).join(Package).join(
        PackageBase).filter(PackageBase.ID == pkgbase.ID)

    # Package dependencies.
    dependencies = db.query(PackageDependency).join(Package).join(
        PackageBase).filter(PackageBase.ID == pkgbase.ID)
    context["dependencies"] = dependencies

    # Package requirements (other packages depend on this one).
    required_by = db.query(PackageDependency).join(Package).filter(
        PackageDependency.DepName == pkgbase.Name).order_by(
        Package.Name.asc())
    context["required_by"] = required_by

    licenses = db.query(License).join(PackageLicense).join(Package).join(
        PackageBase).filter(PackageBase.ID == pkgbase.ID)
    context["licenses"] = licenses

    conflicts = db.query(PackageRelation).join(Package).join(
        PackageBase).filter(
        and_(PackageRelation.RelTypeID == CONFLICTS_ID,
             PackageBase.ID == pkgbase.ID)
    )
    context["conflicts"] = conflicts

    return render_template(request, "packages/show.html", context)


@router.get("/pkgbase/{name}")
async def package_base(request: Request, name: str) -> Response:
    # Get the PackageBase.
    pkgbase = get_pkgbase(name)

    # If this is not a split package, redirect to /packages/{name}.
    if pkgbase.packages.count() == 1:
        return RedirectResponse(f"/packages/{name}",
                                status_code=int(HTTPStatus.SEE_OTHER))

    # Add our base information.
    context = await make_single_context(request, pkgbase)
    context["packages"] = pkgbase.packages.all()

    return render_template(request, "pkgbase.html", context)


@router.get("/pkgbase/{name}/voters")
async def package_base_voters(request: Request, name: str) -> Response:
    # Get the PackageBase.
    pkgbase = get_pkgbase(name)
    context = make_context(request, "Voters")
    context["pkgbase"] = pkgbase
    return render_template(request, "pkgbase/voters.html", context)
