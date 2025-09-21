from fastapi import Request

from aurweb import aur_logging, db, util
from aurweb.auth import creds
from aurweb.models import PackageBase, User
from aurweb.models.package_comaintainer import PackageComaintainer
from aurweb.models.package_notification import PackageNotification
from aurweb.models.request_type import DELETION_ID, MERGE_ID, ORPHAN_ID
from aurweb.packages.requests import handle_request, update_closure_comment
from aurweb.pkgbase import util as pkgbaseutil
from aurweb.scripts import notify, popupdate

logger = aur_logging.get_logger(__name__)


@db.retry_deadlock
def _retry_notify(user: User, pkgbase: PackageBase) -> None:
    with db.begin():
        db.create(PackageNotification, PackageBase=pkgbase, User=user)


def pkgbase_notify_instance(request: Request, pkgbase: PackageBase) -> None:
    notif = db.query(
        pkgbase.notifications.filter(
            PackageNotification.UserID == request.user.ID
        ).exists()
    ).scalar()
    has_cred = request.user.has_credential(creds.PKGBASE_NOTIFY)
    if has_cred and not notif:
        _retry_notify(request.user, pkgbase)


@db.retry_deadlock
def _retry_unnotify(notif: PackageNotification, pkgbase: PackageBase) -> None:
    with db.begin():
        db.delete(notif)


def pkgbase_unnotify_instance(request: Request, pkgbase: PackageBase) -> None:
    notif = pkgbase.notifications.filter(
        PackageNotification.UserID == request.user.ID
    ).first()
    has_cred = request.user.has_credential(creds.PKGBASE_NOTIFY)
    if has_cred and notif:
        _retry_unnotify(notif, pkgbase)


@db.retry_deadlock
def _retry_unflag(pkgbase: PackageBase) -> None:
    with db.begin():
        pkgbase.OutOfDateTS = None
        pkgbase.Flagger = None
        pkgbase.FlaggerComment = str()


def pkgbase_unflag_instance(request: Request, pkgbase: PackageBase) -> None:
    has_cred = request.user.has_credential(
        creds.PKGBASE_UNFLAG,
        approved=[pkgbase.Flagger, pkgbase.Maintainer]
        + [c.User for c in pkgbase.comaintainers],
    )
    if has_cred:
        _retry_unflag(pkgbase)


@db.retry_deadlock
def _retry_disown(request: Request, pkgbase: PackageBase):
    notifs: list[notify.Notification] = []

    is_maint = request.user == pkgbase.Maintainer

    comaint = pkgbase.comaintainers.filter(
        PackageComaintainer.User == request.user
    ).one_or_none()
    is_comaint = comaint is not None

    if is_maint:
        with db.begin():
            # Comaintainer with the lowest Priority value; next-in-line.
            prio_comaint = pkgbase.comaintainers.order_by(
                PackageComaintainer.Priority.asc()
            ).first()
            if prio_comaint:
                # If there is such a comaintainer, promote them to maint.
                pkgbase.Maintainer = prio_comaint.User
                notifs.append(pkgbaseutil.remove_comaintainer(prio_comaint))
            else:
                # Otherwise, just orphan the package completely.
                pkgbase.Maintainer = None
    elif is_comaint:
        # This disown request is from a Comaintainer
        with db.begin():
            notif = pkgbaseutil.remove_comaintainer(comaint)
            notifs.append(notif)
    elif request.user.has_credential(creds.PKGBASE_DISOWN):
        # Otherwise, the request user performing this disownage is a
        # Package Maintainer and we treat it like a standard orphan request.
        notifs += handle_request(request, ORPHAN_ID, pkgbase)
        with db.begin():
            pkgbase.Maintainer = None
            db.delete_all(pkgbase.comaintainers)

    return notifs


def pkgbase_disown_instance(request: Request, pkgbase: PackageBase) -> None:
    disowner = request.user
    notifs = [notify.DisownNotification(disowner.ID, pkgbase.ID)]
    notifs += _retry_disown(request, pkgbase)
    util.apply_all(notifs, lambda n: n.send())


@db.retry_deadlock
def _retry_adopt(request: Request, pkgbase: PackageBase) -> None:
    with db.begin():
        pkgbase.Maintainer = request.user


def pkgbase_adopt_instance(request: Request, pkgbase: PackageBase) -> None:
    _retry_adopt(request, pkgbase)
    notif = notify.AdoptNotification(request.user.ID, pkgbase.ID)
    notif.send()


@db.retry_deadlock
def _retry_delete(pkgbase: PackageBase, comments: str) -> None:
    with db.begin():
        update_closure_comment(pkgbase, DELETION_ID, comments)
        db.delete(pkgbase)


def pkgbase_delete_instance(
    request: Request, pkgbase: PackageBase, comments: str = str()
) -> list[notify.Notification]:
    notif = notify.DeleteNotification(request.user.ID, pkgbase.ID)
    notifs = handle_request(request, DELETION_ID, pkgbase, comments=comments) + [notif]

    _retry_delete(pkgbase, comments)

    return notifs


@db.retry_deadlock
def _retry_merge(pkgbase: PackageBase, target: PackageBase) -> None:
    # Target votes and notifications sets of user IDs that are
    # looking to be migrated.
    target_votes = set(v.UsersID for v in target.package_votes)
    target_notifs = set(n.UserID for n in target.notifications)

    with db.begin():
        # Merge pkgbase's comments.
        for comment in pkgbase.comments:
            comment.PackageBase = target

        # Merge notifications that don't yet exist in the target.
        for notif in pkgbase.notifications:
            if notif.UserID not in target_notifs:
                notif.PackageBase = target

        # Merge votes that don't yet exist in the target.
        for vote in pkgbase.package_votes:
            if vote.UsersID not in target_votes:
                vote.PackageBase = target

    # Run popupdate.
    popupdate.run_single(target)

    with db.begin():
        # Delete pkgbase and its packages now that everything's merged.
        for pkg in pkgbase.packages:
            db.delete(pkg)
        db.delete(pkgbase)


def pkgbase_merge_instance(
    request: Request,
    pkgbase: PackageBase,
    target: PackageBase,
    comments: str = str(),
) -> None:
    pkgbasename = str(pkgbase.Name)

    # Create notifications.
    notifs = handle_request(request, MERGE_ID, pkgbase, target, comments)

    _retry_merge(pkgbase, target)

    # Log this out for accountability purposes.
    logger.info(
        "Package Maintainer '%s' merged '%s' into '%s'.",
        request.user.Username,
        pkgbasename,
        target.Name,
    )

    # Send notifications.
    util.apply_all(notifs, lambda n: n.send())
