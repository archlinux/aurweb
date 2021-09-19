from collections import defaultdict
from http import HTTPStatus
from typing import Dict, List

import orjson

from fastapi import HTTPException
from sqlalchemy import and_, orm

from aurweb import db
from aurweb.models.official_provider import OFFICIAL_BASE, OfficialProvider
from aurweb.models.package import Package
from aurweb.models.package_base import PackageBase
from aurweb.models.package_dependency import PackageDependency
from aurweb.models.package_notification import PackageNotification
from aurweb.models.package_relation import PackageRelation
from aurweb.models.package_vote import PackageVote
from aurweb.models.relation_type import PROVIDES_ID, RelationType
from aurweb.models.user import User
from aurweb.redis import redis_connection
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
    official = db.query(OfficialProvider).filter(
        OfficialProvider.Name == pkgname)
    if official.scalar():
        return f"{base}/?q={pkgname}"
    return f"/packages/{pkgname}"


@register_filter("package_link")
def package_link(package: Package) -> str:
    base = "/".join([OFFICIAL_BASE, "packages"])
    official = db.query(OfficialProvider).filter(
        OfficialProvider.Name == package.Name)
    if official.scalar():
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

    string = ", ".join([
        f'<a href="{package_link(pkg)}">{pkg.Name}</a>'
        for pkg in providers
    ])

    if string:
        # If we actually constructed a string, wrap it.
        string = f"<em>({string})</em>"

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


@register_filter("out_of_date")
def out_of_date(packages: orm.Query) -> orm.Query:
    return packages.filter(PackageBase.OutOfDateTS.isnot(None))


def updated_packages(limit: int = 0, cache_ttl: int = 600) -> List[Package]:
    """ Return a list of valid Package objects ordered by their
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

    query = db.query(Package).join(PackageBase).filter(
        PackageBase.PackagerUID.isnot(None)
    ).order_by(
        PackageBase.ModifiedTS.desc()
    )

    if limit:
        query = query.limit(limit)

    packages = []
    for pkg in query:
        # For each Package returned by the query, append a dict
        # containing Package columns we're interested in.
        packages.append({
            "Name": pkg.Name,
            "Version": pkg.Version,
            "PackageBase": {
                "ModifiedTS": pkg.PackageBase.ModifiedTS
            }
        })

    # Store the JSON serialization of the package_updates key into Redis.
    redis.set("package_updates", orjson.dumps(packages))
    redis.expire("package_updates", cache_ttl)

    # Return the deserialized list of packages.
    return packages


def query_voted(query: List[Package], user: User) -> Dict[int, bool]:
    """ Produce a dictionary of package base ID keys to boolean values,
    which indicate whether or not the package base has a vote record
    related to user.

    :param query: A collection of Package models
    :param user: The user that is being notified or not
    :return: Vote state dict (PackageBase.ID: int -> bool)
    """
    output = defaultdict(bool)
    query_set = {pkg.PackageBase.ID for pkg in query}
    voted = db.query(PackageVote).join(
        PackageBase,
        PackageBase.ID.in_(query_set)
    ).filter(
        PackageVote.UsersID == user.ID
    )
    for vote in voted:
        output[vote.PackageBase.ID] = True
    return output


def query_notified(query: List[Package], user: User) -> Dict[int, bool]:
    """ Produce a dictionary of package base ID keys to boolean values,
    which indicate whether or not the package base has a notification
    record related to user.

    :param query: A collection of Package models
    :param user: The user that is being notified or not
    :return: Notification state dict (PackageBase.ID: int -> bool)
    """
    output = defaultdict(bool)
    query_set = {pkg.PackageBase.ID for pkg in query}
    notified = db.query(PackageNotification).join(
        PackageBase,
        PackageBase.ID.in_(query_set)
    ).filter(
        PackageNotification.UserID == user.ID
    )
    for notify in notified:
        output[notify.PackageBase.ID] = True
    return output
