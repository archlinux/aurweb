from collections import defaultdict
from http import HTTPStatus
from typing import Dict, List, Tuple, Union

import orjson

from fastapi import HTTPException, Request
from sqlalchemy import orm

from aurweb import config, db, l10n, models, util
from aurweb.models import Package, PackageBase, User
from aurweb.models.official_provider import OFFICIAL_BASE, OfficialProvider
from aurweb.models.package_comaintainer import PackageComaintainer
from aurweb.models.package_dependency import PackageDependency
from aurweb.models.package_relation import PackageRelation
from aurweb.redis import redis_connection
from aurweb.scripts import notify
from aurweb.templates import register_filter

Providers = List[Union[PackageRelation, OfficialProvider]]


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
    official = db.query(OfficialProvider).filter(
        OfficialProvider.Name == pkgname).exists()
    if db.query(official).scalar():
        base = "/".join([OFFICIAL_BASE, "packages"])
        return f"{base}/?q={pkgname}"
    return f"/packages/{pkgname}"


@register_filter("package_link")
def package_link(package: Union[Package, OfficialProvider]) -> str:
    if package.is_official:
        base = "/".join([OFFICIAL_BASE, "packages"])
        return f"{base}/?q={package.Name}"
    return f"/packages/{package.Name}"


@register_filter("provides_markup")
def provides_markup(provides: Providers) -> str:
    return ", ".join([
        f'<a href="{package_link(pkg)}">{pkg.Name}</a>'
        for pkg in provides
    ])


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
    query_set = {pkg.PackageBaseID for pkg in query}
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
    query_set = {pkg.PackageBaseID for pkg in query}
    notified = db.query(models.PackageNotification).join(
        models.PackageBase,
        models.PackageBase.ID.in_(query_set)
    ).filter(
        models.PackageNotification.UserID == user.ID
    )
    for notif in notified:
        output[notif.PackageBase.ID] = True
    return output


def remove_comaintainer(comaint: PackageComaintainer) \
        -> notify.ComaintainerRemoveNotification:
    """
    Remove a PackageComaintainer.

    This function does *not* begin any database transaction and
    must be used **within** a database transaction, e.g.:

    with db.begin():
       remove_comaintainer(comaint)

    :param comaint: Target PackageComaintainer to be deleted
    :return: ComaintainerRemoveNotification
    """
    pkgbase = comaint.PackageBase
    notif = notify.ComaintainerRemoveNotification(comaint.User.ID, pkgbase.ID)
    db.delete(comaint)
    rotate_comaintainers(pkgbase)
    return notif


def remove_comaintainers(pkgbase: PackageBase, usernames: List[str]) -> None:
    """
    Remove comaintainers from `pkgbase`.

    :param pkgbase: PackageBase instance
    :param usernames: Iterable of username strings
    """
    notifications = []
    with db.begin():
        comaintainers = pkgbase.comaintainers.join(User).filter(
            User.Username.in_(usernames)
        ).all()
        notifications = [
            notify.ComaintainerRemoveNotification(co.User.ID, pkgbase.ID)
            for co in comaintainers
        ]
        db.delete_all(comaintainers)

    # Rotate comaintainer priority values.
    with db.begin():
        rotate_comaintainers(pkgbase)

    # Send out notifications.
    util.apply_all(notifications, lambda n: n.send())


def latest_priority(pkgbase: PackageBase) -> int:
    """
    Return the highest Priority column related to `pkgbase`.

    :param pkgbase: PackageBase instance
    :return: Highest Priority found or 0 if no records exist
    """

    # Order comaintainers related to pkgbase by Priority DESC.
    record = pkgbase.comaintainers.order_by(
        PackageComaintainer.Priority.desc()).first()

    # Use Priority column if record exists, otherwise 0.
    return record.Priority if record else 0


class NoopComaintainerNotification:
    """ A noop notification stub used as an error-state return value. """

    def send(self) -> None:
        """ noop """
        return


def add_comaintainer(pkgbase: PackageBase, comaintainer: User) \
        -> notify.ComaintainerAddNotification:
    """
    Add a new comaintainer to `pkgbase`.

    :param pkgbase: PackageBase instance
    :param comaintainer: User instance used for new comaintainer record
    :return: ComaintainerAddNotification
    """
    # Skip given `comaintainers` who are already maintainer.
    if pkgbase.Maintainer == comaintainer:
        return NoopComaintainerNotification()

    # Priority for the new comaintainer is +1 more than the highest.
    new_prio = latest_priority(pkgbase) + 1

    with db.begin():
        db.create(PackageComaintainer, PackageBase=pkgbase,
                  User=comaintainer, Priority=new_prio)

    return notify.ComaintainerAddNotification(comaintainer.ID, pkgbase.ID)


def add_comaintainers(request: Request, pkgbase: models.PackageBase,
                      usernames: List[str]) -> None:
    """
    Add comaintainers to `pkgbase`.

    :param request: FastAPI request
    :param pkgbase: PackageBase instance
    :param usernames: Iterable of username strings
    :return: Error string on failure else None
    """
    # For each username in usernames, perform validation of the username
    # and append the User record to `users` if no errors occur.
    users = []
    for username in usernames:
        user = db.query(User).filter(User.Username == username).first()
        if not user:
            _ = l10n.get_translator_for_request(request)
            return _("Invalid user name: %s") % username
        users.append(user)

    notifications = []

    def add_comaint(user: User):
        nonlocal notifications
        # Populate `notifications` with add_comaintainer's return value,
        # which is a ComaintainerAddNotification.
        notifications.append(add_comaintainer(pkgbase, user))

    # Move along: add all `users` as new `pkgbase` comaintainers.
    util.apply_all(users, add_comaint)

    # Send out notifications.
    util.apply_all(notifications, lambda n: n.send())


def rotate_comaintainers(pkgbase: PackageBase) -> None:
    """
    Rotate `pkgbase` comaintainers.

    This function resets the Priority column of all PackageComaintainer
    instances related to `pkgbase` to seqential 1 .. n values with
    persisted order.

    :param pkgbase: PackageBase instance
    """
    comaintainers = pkgbase.comaintainers.order_by(
        models.PackageComaintainer.Priority.asc())
    for i, comaint in enumerate(comaintainers):
        comaint.Priority = i + 1


def pkg_required(pkgname: str, provides: List[str], limit: int) \
        -> List[PackageDependency]:
    """
    Get dependencies that match a string in `[pkgname] + provides`.

    :param pkgname: Package.Name
    :param provides: List of PackageRelation.Name
    :param limit: Maximum number of dependencies to query
    :return: List of PackageDependency instances
    """
    targets = set([pkgname] + provides)
    query = db.query(PackageDependency).join(Package).filter(
        PackageDependency.DepName.in_(targets)
    ).order_by(Package.Name.asc()).limit(limit)
    return query.all()


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
    :return (text, uri) tuple
    """
    if "::" in pkgsrc.Source:
        return pkgsrc.Source.split("::", 1)
    elif "://" in pkgsrc.Source:
        return (pkgsrc.Source, pkgsrc.Source)
    path = config.get("options", "source_file_uri")
    pkgbasename = pkgsrc.Package.PackageBase.Name
    return (pkgsrc.Source, path % (pkgsrc.Source, pkgbasename))
