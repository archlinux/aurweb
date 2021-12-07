from collections import defaultdict
from http import HTTPStatus
from typing import Dict, List, Union

import orjson

from fastapi import HTTPException, Request
from sqlalchemy import and_, orm

from aurweb import db, l10n, models, util
from aurweb.models.official_provider import OFFICIAL_BASE
from aurweb.models.relation_type import PROVIDES_ID
from aurweb.redis import redis_connection
from aurweb.scripts import notify
from aurweb.templates import register_filter


def dep_depends_extra(dep: models.PackageDependency) -> str:
    """ A function used to produce extra text for dependency display. """
    return str()


def dep_makedepends_extra(dep: models.PackageDependency) -> str:
    """ A function used to produce extra text for dependency display. """
    return "(make)"


def dep_checkdepends_extra(dep: models.PackageDependency) -> str:
    """ A function used to produce extra text for dependency display. """
    return "(check)"


def dep_optdepends_extra(dep: models.PackageDependency) -> str:
    """ A function used to produce extra text for dependency display. """
    return "(optional)"


@register_filter("dep_extra")
def dep_extra(dep: models.PackageDependency) -> str:
    """ Some dependency types have extra text added to their
    display. This function provides that output. However, it
    **assumes** that the dep passed is bound to a valid one
    of: depends, makedepends, checkdepends or optdepends. """
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
    base = "/".join([OFFICIAL_BASE, "packages"])
    official = db.query(models.OfficialProvider).filter(
        models.OfficialProvider.Name == pkgname).exists()
    if db.query(official).scalar():
        return f"{base}/?q={pkgname}"
    return f"/packages/{pkgname}"


@register_filter("package_link")
def package_link(package: models.Package) -> str:
    base = "/".join([OFFICIAL_BASE, "packages"])
    official = db.query(models.OfficialProvider).filter(
        models.OfficialProvider.Name == package.Name).exists()
    if db.query(official).scalar():
        return f"{base}/?q={package.Name}"
    return f"/packages/{package.Name}"


@register_filter("provides_list")
def provides_list(package: models.Package, depname: str) -> list:
    providers = db.query(models.Package).join(
        models.PackageRelation).join(models.RelationType).filter(
        and_(
            models.PackageRelation.RelName == depname,
            models.RelationType.ID == PROVIDES_ID
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


def get_pkg_or_base(
        name: str,
        cls: Union[models.Package, models.PackageBase] = models.PackageBase):
    """ Get a PackageBase instance by its name or raise a 404 if
    it can't be found in the database.

    :param name: {Package,PackageBase}.Name
    :raises HTTPException: With status code 404 if record doesn't exist
    :return: {Package,PackageBase} instance
    """
    provider = db.query(models.OfficialProvider).filter(
        models.OfficialProvider.Name == name).first()
    if provider:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND)

    instance = db.query(cls).filter(cls.Name == name).first()
    if not instance:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND)

    return db.refresh(instance)


def get_pkgbase_comment(pkgbase: models.PackageBase, id: int) \
        -> models.PackageComment:
    comment = pkgbase.comments.filter(models.PackageComment.ID == id).first()
    if not comment:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND)
    return db.refresh(comment)


def get_pkgreq_by_id(id: int):
    pkgreq = db.query(models.PackageRequest).filter(
        models.PackageRequest.ID == id).first()
    if not pkgreq:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND)
    return db.refresh(pkgreq)


@register_filter("out_of_date")
def out_of_date(packages: orm.Query) -> orm.Query:
    return packages.filter(models.PackageBase.OutOfDateTS.isnot(None))


def updated_packages(limit: int = 0,
                     cache_ttl: int = 600) -> List[models.Package]:
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

    query = db.query(models.Package).join(models.PackageBase).filter(
        models.PackageBase.PackagerUID.isnot(None)
    ).order_by(
        models.PackageBase.ModifiedTS.desc()
    )

    if limit:
        query = query.limit(limit)

    packages = []
    for pkg in query:
        # For each Package returned by the query, append a dict
        # containing Package columns we're interested in.
        db.refresh(pkg)
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


def query_voted(query: List[models.Package],
                user: models.User) -> Dict[int, bool]:
    """ Produce a dictionary of package base ID keys to boolean values,
    which indicate whether or not the package base has a vote record
    related to user.

    :param query: A collection of Package models
    :param user: The user that is being notified or not
    :return: Vote state dict (PackageBase.ID: int -> bool)
    """
    output = defaultdict(bool)
    query_set = {pkg.PackageBase.ID for pkg in query}
    voted = db.query(models.PackageVote).join(
        models.PackageBase,
        models.PackageBase.ID.in_(query_set)
    ).filter(
        models.PackageVote.UsersID == user.ID
    )
    for vote in voted:
        output[vote.PackageBase.ID] = True
    return output


def query_notified(query: List[models.Package],
                   user: models.User) -> Dict[int, bool]:
    """ Produce a dictionary of package base ID keys to boolean values,
    which indicate whether or not the package base has a notification
    record related to user.

    :param query: A collection of Package models
    :param user: The user that is being notified or not
    :return: Notification state dict (PackageBase.ID: int -> bool)
    """
    output = defaultdict(bool)
    query_set = {pkg.PackageBase.ID for pkg in query}
    notified = db.query(models.PackageNotification).join(
        models.PackageBase,
        models.PackageBase.ID.in_(query_set)
    ).filter(
        models.PackageNotification.UserID == user.ID
    )
    for notif in notified:
        output[notif.PackageBase.ID] = True
    return output


def remove_comaintainers(pkgbase: models.PackageBase,
                         usernames: List[str]) -> None:
    """
    Remove comaintainers from `pkgbase`.

    :param pkgbase: PackageBase instance
    :param usernames: Iterable of username strings
    :return: None
    """
    notifications = []
    with db.begin():
        for username in usernames:
            # We know that the users we passed here are in the DB.
            # No need to check for their existence.
            comaintainer = pkgbase.comaintainers.join(models.User).filter(
                models.User.Username == username
            ).first()
            notifications.append(
                notify.ComaintainerRemoveNotification(
                    comaintainer.User.ID, pkgbase.ID)
            )
            db.delete(comaintainer)

    # Send out notifications if need be.
    util.apply_all(notifications, lambda n: n.send())


def add_comaintainers(request: Request, pkgbase: models.PackageBase,
                      priority: int, usernames: List[str]) -> None:
    """
    Add comaintainers to `pkgbase`.

    :param request: FastAPI request
    :param pkgbase: PackageBase instance
    :param priority: Initial priority value
    :param usernames: Iterable of username strings
    :return: None on success, an error string on failure
    """

    # First, perform a check against all usernames given; for each
    # username, add its related User object to memo.
    _ = l10n.get_translator_for_request(request)
    memo = {}
    for username in usernames:
        user = db.query(models.User).filter(
            models.User.Username == username).first()
        if not user:
            return _("Invalid user name: %s") % username
        memo[username] = user

    # Alright, now that we got past the check, add them all to the DB.
    notifications = []
    with db.begin():
        for username in usernames:
            user = memo.get(username)
            if pkgbase.Maintainer == user:
                # Already a maintainer. Move along.
                continue

            # If we get here, our user model object is in the memo.
            comaintainer = db.create(
                models.PackageComaintainer,
                PackageBase=pkgbase,
                User=user,
                Priority=priority)
            priority += 1

            notifications.append(
                notify.ComaintainerAddNotification(
                    comaintainer.User.ID, pkgbase.ID)
            )

    # Send out notifications.
    util.apply_all(notifications, lambda n: n.send())
