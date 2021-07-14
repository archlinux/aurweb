from http import HTTPStatus

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse

import aurweb.models.package
import aurweb.models.package_comment
import aurweb.models.package_keyword

from aurweb import db
from aurweb.models.package_base import PackageBase
from aurweb.templates import make_variable_context, render_template

router = APIRouter()


@router.get("/packages/{package}")
async def package_base(request: Request, package: str):
    package = db.query(PackageBase).filter(PackageBase.Name == package).first()
    if not package:
        raise HTTPException(status_code=int(HTTPStatus.NOT_FOUND))

    context = await make_variable_context(request, package.Name)
    context["git_clone_uri_anon"] = aurweb.config.get("options", "git_clone_uri_anon")
    context["git_clone_uri_priv"] = aurweb.config.get("options", "git_clone_uri_priv")
    context["pkgbase"] = package
    context["packages"] = package.packages.all()
    context["packages_count"] = package.packages.count()
    context["keywords"] = package.keywords.all()
    context["comments"] = package.comments.all()
    context["is_maintainer"] = request.user.is_authenticated() \
        and request.user.Username == package.Maintainer.Username

    return render_template(request, "pkgbase.html", context)


@router.get("/pkgbase/{package}")
async def package_base_redirect(request: Request, package: str):
    return RedirectResponse(f"/packages/{package}")
