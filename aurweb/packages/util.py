from collections import defaultdict
from http import HTTPStatus
from typing import Tuple, Union
from urllib.parse import quote_plus

import orjson
from fastapi import HTTPException
from sqlalchemy import and_, literal, orm

from aurweb import config, db, models
from aurweb.aur_redis import redis_connection
from aurweb.models import Package
from aurweb.models.official_provider import OFFICIAL_BASE, OfficialProvider
from aurweb.models.package_dependency import PackageDependency
from aurweb.models.package_relation import PackageRelation
from aurweb.models.relation_type import PROVIDES_ID
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
def pkgname_link(
    pkgname: str, aur_packages: set[str], official_packages: set[str]
) -> str:
    if pkgname in aur_packages:
        return f"/packages/{pkgname}"

    if pkgname in official_packages:
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
    instance = db.query(cls).filter(cls.Name == name).first()
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


def query_package_dependencies(
    pkg: Package, all_deps: bool, max_listing: int = 20
) -> tuple[list[PackageDependency], int]:
    """
    Get dependencies of a given package

    :param pkg: Package to query the dependencies for
    :param all_deps: Bool if all dependencies should be fetched
    :param max_listing: Maximum numbers to fetch
    :return: tuple of a List of PackageDependency and total count
    """
    dependencies_query = pkg.package_dependencies.order_by(
        PackageDependency.DepTypeID.asc(), PackageDependency.DepName.asc()
    )

    if all_deps:
        dependencies = dependencies_query.all()
        total_count = len(dependencies)
        return dependencies, total_count

    dependencies = dependencies_query.limit(max_listing).all()
    total_count = len(dependencies)

    # if the fetched count equals the limit, check the total count with no limits
    if total_count >= max_listing:
        total_count = dependencies_query.count()

    return dependencies, total_count


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
        .order_by(Package.Name.asc(), PackageDependency.DepTypeID.asc())
    )
    return query


def query_required_by_package_dependencies(
    pkg: Package,
    provides: list[PackageRelation],
    all_reqs: bool,
    max_listing: int = 20,
) -> tuple[list[PackageDependency], int]:
    """
    Get PackageDependency model for all relations requiring a given
    package or any of its provides.

    :param pkg: Package to query the required by dependencies
    :param provides: List of PackageRelation that the given Package provides
    :param all_reqs: Bool if all required by dependencies should be fetched
    :param max_listing: Maximum numbers to fetch
    :return: tuple of a List of PackageDependency and total count
    """
    required_by_query = pkg_required(pkg.Name, [p.RelName for p in provides])

    if all_reqs:
        required_by = required_by_query.all()
        total_count = len(required_by)
        return required_by, total_count

    required_by = required_by_query.limit(max_listing).all()
    total_count = len(required_by)

    # if the fetched count equals the limit, check the total count with no limits
    if total_count >= max_listing:
        total_count = required_by_query.count()

    return required_by, total_count


def lookup_aur_packages(dependency_names: list[str]) -> set[str]:
    """
    Returns a set of all dependency names which are AUR packages.

    :param dependency_names: List of dependency names for which to do the lookup
    :return: set of package names that can be looked up in the AUR
    """
    aur_dep_packages_query = (
        db.query(models.Package)
        .with_entities(
            models.Package.Name.label("DepName"),
        )
        .filter(models.Package.Name.in_(dependency_names))
    )
    return set([dep.DepName for dep in aur_dep_packages_query.all()])


def lookup_dependencies(
    dependency_names: list[str],
) -> Tuple[set[str], set[str], dict[str, dict[str, str]]]:
    """
    Efficient lookup all given dependency names and return distinct sets for AUR
    and official packages as well as a dict for all AUR and official packages
    providing the dependency name via the provides property.

    :param dependency_names: List of dependency names for which to do the lookup
    :return: set of AUR packages, set of official packages, dict of providers
    """
    aur_dep_provides_query = (
        db.query(models.PackageRelation)
        .join(models.Package)
        .with_entities(
            models.Package.Name.label("Name"),
            models.PackageRelation.RelName.label("provides"),
            literal(False).label("is_official"),
        )
        .filter(
            and_(
                models.PackageRelation.RelTypeID == PROVIDES_ID,
                models.PackageRelation.RelName.in_(dependency_names),
            )
        )
        .order_by(models.Package.Name.asc())
    )

    official_dep_provides_query = (
        db.query(models.OfficialProvider)
        .with_entities(
            models.OfficialProvider.Name.label("Name"),
            models.OfficialProvider.Provides.label("provides"),
            literal(True).label("is_official"),
        )
        .filter(models.OfficialProvider.Provides.in_(dependency_names))
        .order_by(models.OfficialProvider.Name.asc())
    )

    combined_provider = aur_dep_provides_query.union_all(
        official_dep_provides_query
    ).all()

    aur_packages = lookup_aur_packages(dependency_names)
    dependency_providers = defaultdict(list)
    official_packages = set()

    for provider in combined_provider:
        if provider.is_official:
            official_packages.add(provider.Name)
            if provider.provides == provider.Name:
                continue
        dependency_providers[provider.provides].append(provider)

    return aur_packages, official_packages, dependency_providers


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
