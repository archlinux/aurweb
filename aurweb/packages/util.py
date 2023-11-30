from collections import defaultdict
from http import HTTPStatus
from typing import Tuple, Union
from urllib.parse import quote_plus

import orjson
from fastapi import HTTPException
from sqlalchemy import orm

from aurweb import config, db, models
from aurweb.aur_redis import redis_connection
from aurweb.models import Package
from aurweb.models.official_provider import OFFICIAL_BASE, OfficialProvider
from aurweb.models.package_dependency import PackageDependency
from aurweb.models.package_relation import PackageRelation
from aurweb.templates import register_filter

Providers = list[Union[PackageRelation, OfficialProvider]]


def dep_extra_with_arch(dep: models.PackageDependency, annotation: str) -> str:
    output = [annotation]
    if dep.DepArch:
        output.append(dep.DepArch)
    return f"({', '.join(output)})"


def dep_depends_extra(dep: models.PackageDependency) -> str:
    return str()


def dep_makedepends_extra(dep: models.PackageDependency) -> str:
    return dep_extra_with_arch(dep, "make")


def dep_checkdepends_extra(dep: models.PackageDependency) -> str:
    return dep_extra_with_arch(dep, "check")


def dep_optdepends_extra(dep: models.PackageDependency) -> str:
    return dep_extra_with_arch(dep, "optional")


@register_filter("dep_extra")
def dep_extra(dep: models.PackageDependency) -> str:
    """Some dependency types have extra text added to their
    display. This function provides that output. However, it
    **assumes** that the dep passed is bound to a valid one
    of: depends, makedepends, checkdepends or optdepends."""
    f = globals().get(f"dep_{dep.DependencyType.Name}_extra")
    return f(dep)


@register_filter("dep_extra_desc")
def dep_extra_desc(dep: models.PackageDependency) -> str:
    extra = dep_extra(dep)
    if not dep.DepDesc:
        return extra
    return extra + f" – {dep.DepDesc}"


@register_filter("pkgname_link")
def pkgname_link(pkgname: str) -> str:
    record = db.query(Package).filter(Package.Name == pkgname).exists()
    if db.query(record).scalar():
        return f"/packages/{pkgname}"

    official = (
        db.query(OfficialProvider).filter(OfficialProvider.Name == pkgname).exists()
    )
    if db.query(official).scalar():
        base = "/".join([OFFICIAL_BASE, "packages"])
        return f"{base}/?q={pkgname}"


@register_filter("package_link")
def package_link(package: Union[Package, OfficialProvider]) -> str:
    if package.is_official:
        base = "/".join([OFFICIAL_BASE, "packages"])
        return f"{base}/?q={package.Name}"
    return f"/packages/{package.Name}"


@register_filter("provides_markup")
def provides_markup(provides: Providers) -> str:
    links = []
    for pkg in provides:
        aur = "<sup><small>AUR</small></sup>" if not pkg.is_official else ""
        links.append(f'<a href="{package_link(pkg)}">{pkg.Name}</a>{aur}')
    return ", ".join(links)


def get_pkg_or_base(
    name: str, cls: Union[models.Package, models.PackageBase] = models.PackageBase
) -> Union[models.Package, models.PackageBase]:
    """Get a PackageBase instance by its name or raise a 404 if
    it can't be found in the database.

    :param name: {Package,PackageBase}.Name
    :param exception: Whether to raise an HTTPException or simply return None if
                      the package can't be found.
    :raises HTTPException: With status code 404 if record doesn't exist
    :return: {Package,PackageBase} instance
    """
    instance = db.query(cls).filter(cls.Name == name.lower()).first()
    if not instance:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND)
    return instance


def get_pkgbase_comment(pkgbase: models.PackageBase, id: int) -> models.PackageComment:
    comment = pkgbase.comments.filter(models.PackageComment.ID == id).first()
    if not comment:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND)
    return db.refresh(comment)


@register_filter("out_of_date")
def out_of_date(packages: orm.Query) -> orm.Query:
    return packages.filter(models.PackageBase.OutOfDateTS.isnot(None))


def updated_packages(limit: int = 0, cache_ttl: int = 600) -> list[models.Package]:
    """Return a list of valid Package objects ordered by their
    ModifiedTS column in descending order from cache, after setting
    the cache when no key yet exists.

    :param limit: Optional record limit
    :param cache_ttl: Cache expiration time (in seconds)
    :return: A list of Packages
    """
    redis = redis_connection()
    packages = redis.get("package_updates")
    if packages:
        # If we already have a cache, deserialize it and return.
        return orjson.loads(packages)

    query = (
        db.query(models.Package)
        .join(models.PackageBase)
        .order_by(models.PackageBase.ModifiedTS.desc())
    )

    if limit:
        query = query.limit(limit)

    packages = []
    for pkg in query:
        # For each Package returned by the query, append a dict
        # containing Package columns we're interested in.
        packages.append(
            {
                "Name": pkg.Name,
                "Version": pkg.Version,
                "PackageBase": {"ModifiedTS": pkg.PackageBase.ModifiedTS},
            }
        )

    # Store the JSON serialization of the package_updates key into Redis.
    redis.set("package_updates", orjson.dumps(packages))
    redis.expire("package_updates", cache_ttl)

    # Return the deserialized list of packages.
    return packages


def query_voted(query: list[models.Package], user: models.User) -> dict[int, bool]:
    """Produce a dictionary of package base ID keys to boolean values,
    which indicate whether or not the package base has a vote record
    related to user.

    :param query: A collection of Package models
    :param user: The user that is being notified or not
    :return: Vote state dict (PackageBase.ID: int -> bool)
    """
    output = defaultdict(bool)
    query_set = {pkg.PackageBaseID for pkg in query}
    voted = (
        db.query(models.PackageVote)
        .join(models.PackageBase, models.PackageBase.ID.in_(query_set))
        .filter(models.PackageVote.UsersID == user.ID)
    )
    for vote in voted:
        output[vote.PackageBase.ID] = True
    return output


def query_notified(query: list[models.Package], user: models.User) -> dict[int, bool]:
    """Produce a dictionary of package base ID keys to boolean values,
    which indicate whether or not the package base has a notification
    record related to user.

    :param query: A collection of Package models
    :param user: The user that is being notified or not
    :return: Notification state dict (PackageBase.ID: int -> bool)
    """
    output = defaultdict(bool)
    query_set = {pkg.PackageBaseID for pkg in query}
    notified = (
        db.query(models.PackageNotification)
        .join(models.PackageBase, models.PackageBase.ID.in_(query_set))
        .filter(models.PackageNotification.UserID == user.ID)
    )
    for notif in notified:
        output[notif.PackageBase.ID] = True
    return output


def pkg_required(pkgname: str, provides: list[str]) -> list[PackageDependency]:
    """
    Get dependencies that match a string in `[pkgname] + provides`.

    :param pkgname: Package.Name
    :param provides: List of PackageRelation.Name
    :param limit: Maximum number of dependencies to query
    :return: List of PackageDependency instances
    """
    targets = set([pkgname] + provides)
    query = (
        db.query(PackageDependency)
        .join(Package)
        .options(orm.contains_eager(PackageDependency.Package))
        .filter(PackageDependency.DepName.in_(targets))
        .order_by(Package.Name.asc())
    )
    return query


@register_filter("source_uri")
def source_uri(pkgsrc: models.PackageSource) -> Tuple[str, str]:
    """
    Produce a (text, uri) tuple out of `pkgsrc`.

    In this filter, we cover various cases:
    1. If "::" is anywhere in the Source column, split the string,
       which should produce a (text, uri), where text is before "::"
       and uri is after "::".
    2. Otherwise, if "://" is anywhere in the Source column, it's just
       some sort of URI, which we'll return varbatim as both text and uri.
    3. Otherwise, we'll return a path to the source file in a uri produced
       out of options.source_file_uri formatted with the source file and
       the package base name.

    :param pkgsrc: PackageSource instance
    :return text, uri)tuple
    """
    if "::" in pkgsrc.Source:
        return pkgsrc.Source.split("::", 1)
    elif "://" in pkgsrc.Source:
        return pkgsrc.Source, pkgsrc.Source
    path = config.get("options", "source_file_uri")
    pkgbasename = quote_plus(pkgsrc.Package.PackageBase.Name)
    return pkgsrc.Source, path % (pkgsrc.Source, pkgbasename)
