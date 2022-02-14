from typing import Any, Dict, List

from fastapi import Request
from sqlalchemy import and_

from aurweb import config, db, l10n, util
from aurweb.models import PackageBase, User
from aurweb.models.package_comaintainer import PackageComaintainer
from aurweb.models.package_comment import PackageComment
from aurweb.models.package_request import PENDING_ID, PackageRequest
from aurweb.models.package_vote import PackageVote
from aurweb.scripts import notify
from aurweb.templates import make_context as _make_context


def make_context(request: Request, pkgbase: PackageBase) -> Dict[str, Any]:
    """ Make a basic context for package or pkgbase.

    :param request: FastAPI request
    :param pkgbase: PackageBase instance
    :return: A pkgbase context without specific differences
    """
    context = _make_context(request, pkgbase.Name)

    context["git_clone_uri_anon"] = config.get("options", "git_clone_uri_anon")
    context["git_clone_uri_priv"] = config.get("options", "git_clone_uri_priv")
    context["pkgbase"] = pkgbase
    context["comaintainers"] = [
        c.User for c in pkgbase.comaintainers.order_by(
            PackageComaintainer.Priority.asc()
        ).all()
    ]
    context["packages_count"] = pkgbase.packages.count()
    context["keywords"] = pkgbase.keywords
    context["comments"] = pkgbase.comments.order_by(
        PackageComment.CommentTS.desc()
    )
    context["pinned_comments"] = pkgbase.comments.filter(
        PackageComment.PinnedTS != 0
    ).order_by(PackageComment.CommentTS.desc())

    context["is_maintainer"] = bool(request.user == pkgbase.Maintainer)
    context["notified"] = request.user.notified(pkgbase)

    context["out_of_date"] = bool(pkgbase.OutOfDateTS)

    context["voted"] = request.user.package_votes.filter(
        PackageVote.PackageBaseID == pkgbase.ID
    ).scalar()

    context["requests"] = pkgbase.requests.filter(
        and_(PackageRequest.Status == PENDING_ID,
             PackageRequest.ClosedTS.is_(None))
    ).count()

    return context


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


def add_comaintainers(request: Request, pkgbase: PackageBase,
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
        PackageComaintainer.Priority.asc())
    for i, comaint in enumerate(comaintainers):
        comaint.Priority = i + 1
