from http import HTTPStatus
from typing import Any, Dict

from fastapi import APIRouter, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy import and_

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
from aurweb.models.package_source import PackageSource
from aurweb.models.package_vote import PackageVote
from aurweb.models.relation_type import CONFLICTS_ID, RelationType
from aurweb.packages.util import get_pkgbase
from aurweb.templates import make_variable_context, render_template

router = APIRouter()


async def make_single_context(request: Request,
                              pkgbase: PackageBase) -> Dict[str, Any]:
    """ Make a basic context for package or pkgbase.

    :param request: FastAPI request
    :param pkgbase: PackageBase instance
    :return: A pkgbase context without specific differences
    """
    context = await make_variable_context(request, pkgbase.Name)
    context["git_clone_uri_anon"] = aurweb.config.get("options",
                                                      "git_clone_uri_anon")
    context["git_clone_uri_priv"] = aurweb.config.get("options",
                                                      "git_clone_uri_priv")
    context["pkgbase"] = pkgbase
    context["packages_count"] = pkgbase.packages.count()
    context["keywords"] = pkgbase.keywords
    context["comments"] = pkgbase.comments
    context["is_maintainer"] = (request.user.is_authenticated()
                                and request.user == pkgbase.Maintainer)
    context["notified"] = db.query(
        PackageNotification).join(PackageBase).filter(
        and_(PackageBase.ID == pkgbase.ID,
             PackageNotification.UserID == request.user.ID)).count() > 0

    context["out_of_date"] = bool(pkgbase.OutOfDateTS)

    context["voted"] = pkgbase.package_votes.filter(
        PackageVote.UsersID == request.user.ID).count() > 0

    context["notifications_enabled"] = db.query(
        PackageNotification).join(PackageBase).filter(
        PackageBase.ID == pkgbase.ID).count() > 0

    return context


@router.get("/packages/{name}")
async def package(request: Request, name: str) -> Response:
    # Get the PackageBase.
    pkgbase = get_pkgbase(name)

    # Add our base information.
    context = await make_single_context(request, pkgbase)

    # Package sources.
    sources = db.query(PackageSource).join(Package).filter(
        Package.PackageBaseID == pkgbase.ID)
    context["sources"] = sources

    # Package dependencies.
    dependencies = db.query(PackageDependency).join(Package).filter(
        Package.PackageBaseID == pkgbase.ID)
    context["dependencies"] = dependencies

    # Package requirements (other packages depend on this one).
    required_by = db.query(PackageDependency).join(Package).filter(
        PackageDependency.DepName == pkgbase.Name).order_by(
        Package.Name.asc())
    context["required_by"] = required_by

    licenses = db.query(License).join(PackageLicense).join(Package).filter(
        PackageLicense.PackageID == pkgbase.packages.first().ID)
    context["licenses"] = licenses

    conflicts = db.query(PackageRelation).join(RelationType).join(Package).join(PackageBase).filter(
        and_(RelationType.ID == CONFLICTS_ID,
             PackageBase.ID == pkgbase.ID))
    context["conflicts"] = conflicts

    return render_template(request, "packages/show.html", context)
