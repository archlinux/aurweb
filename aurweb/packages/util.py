from http import HTTPStatus

from fastapi import HTTPException
from sqlalchemy import and_

from aurweb import db
from aurweb.models.official_provider import OFFICIAL_BASE, OfficialProvider
from aurweb.models.package import Package
from aurweb.models.package_base import PackageBase
from aurweb.models.package_dependency import PackageDependency
from aurweb.models.package_relation import PackageRelation
from aurweb.models.relation_type import PROVIDES_ID, RelationType
from aurweb.templates import register_filter


def dep_depends_extra(dep: PackageDependency) -> str:
    """ A function used to produce extra text for dependency display. """
    return str()


def dep_makedepends_extra(dep: PackageDependency) -> str:
    """ A function used to produce extra text for dependency display. """
    return "(make)"


def dep_checkdepends_extra(dep: PackageDependency) -> str:
    """ A function used to produce extra text for dependency display. """
    return "(check)"


def dep_optdepends_extra(dep: PackageDependency) -> str:
    """ A function used to produce extra text for dependency display. """
    return "(optional)"


@register_filter("dep_extra")
def dep_extra(dep: PackageDependency) -> str:
    """ Some dependency types have extra text added to their
    display. This function provides that output. However, it
    **assumes** that the dep passed is bound to a valid one
    of: depends, makedepends, checkdepends or optdepends. """
    f = globals().get(f"dep_{dep.DependencyType.Name}_extra")
    return f(dep)


@register_filter("dep_extra_desc")
def dep_extra_desc(dep: PackageDependency) -> str:
    extra = dep_extra(dep)
    if not dep.DepDesc:
        return extra
    return extra + f" – {dep.DepDesc}"


@register_filter("pkgname_link")
def pkgname_link(pkgname: str) -> str:
    base = "/".join([OFFICIAL_BASE, "packages"])
    pkg = db.query(Package).filter(Package.Name == pkgname)
    official = db.query(OfficialProvider).filter(
        OfficialProvider.Name == pkgname)
    if not pkg.count() or official.count():
        return f"{base}/?q={pkgname}"
    return f"/packages/{pkgname}"


@register_filter("package_link")
def package_link(package: Package) -> str:
    base = "/".join([OFFICIAL_BASE, "packages"])
    official = db.query(OfficialProvider).filter(
        OfficialProvider.Name == package.Name)
    if official.count():
        return f"{base}/?q={package.Name}"
    return f"/packages/{package.Name}"


@register_filter("provides_list")
def provides_list(package: Package, depname: str) -> list:
    providers = db.query(Package).join(
        PackageRelation).join(RelationType).filter(
        and_(
            PackageRelation.RelName == depname,
            RelationType.ID == PROVIDES_ID
        )
    )

    string = str()
    has_providers = providers.count() > 0

    if has_providers:
        string += "<em>("

    string += ", ".join([
        f'<a href="{package_link(pkg)}">{pkg.Name}</a>'
        for pkg in providers
    ])

    if has_providers:
        string += ")</em>"

    return string


def get_pkgbase(name: str) -> PackageBase:
    """ Get a PackageBase instance by its name or raise a 404 if
    it can't be foudn in the database.

    :param name: PackageBase.Name
    :raises HTTPException: With status code 404 if PackageBase doesn't exist
    :return: PackageBase instance
    """
    pkgbase = db.query(PackageBase).filter(PackageBase.Name == name).first()
    if not pkgbase:
        raise HTTPException(status_code=int(HTTPStatus.NOT_FOUND))

    provider = db.query(OfficialProvider).filter(
        OfficialProvider.Name == name).first()
    if provider:
        raise HTTPException(status_code=int(HTTPStatus.NOT_FOUND))

    return pkgbase
