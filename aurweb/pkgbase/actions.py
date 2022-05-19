from typing import List

from fastapi import Request

from aurweb import db, logging, util
from aurweb.auth import creds
from aurweb.models import PackageBase
from aurweb.models.package_comaintainer import PackageComaintainer
from aurweb.models.package_notification import PackageNotification
from aurweb.models.request_type import DELETION_ID, MERGE_ID, ORPHAN_ID
from aurweb.packages.requests import handle_request, update_closure_comment
from aurweb.pkgbase import util as pkgbaseutil
from aurweb.scripts import notify, popupdate

logger = logging.get_logger(__name__)


def pkgbase_notify_instance(request: Request, pkgbase: PackageBase) -> None:
    notif = db.query(pkgbase.notifications.filter(
        PackageNotification.UserID == request.user.ID
    ).exists()).scalar()
    has_cred = request.user.has_credential(creds.PKGBASE_NOTIFY)
    if has_cred and not notif:
        with db.begin():
            db.create(PackageNotification,
                      PackageBase=pkgbase,
                      User=request.user)


def pkgbase_unnotify_instance(request: Request, pkgbase: PackageBase) -> None:
    notif = pkgbase.notifications.filter(
        PackageNotification.UserID == request.user.ID
    ).first()
    has_cred = request.user.has_credential(creds.PKGBASE_NOTIFY)
    if has_cred and notif:
        with db.begin():
            db.delete(notif)


def pkgbase_unflag_instance(request: Request, pkgbase: PackageBase) -> None:
    has_cred = request.user.has_credential(creds.PKGBASE_UNFLAG, approved=[
                                           pkgbase.Flagger, pkgbase.Maintainer] + [c.User for c in pkgbase.comaintainers])
    if has_cred:
        with db.begin():
            pkgbase.OutOfDateTS = None
            pkgbase.Flagger = None
            pkgbase.FlaggerComment = str()


def pkgbase_disown_instance(request: Request, pkgbase: PackageBase) -> None:
    disowner = request.user
    notifs = [notify.DisownNotification(disowner.ID, pkgbase.ID)]

    is_maint = disowner == pkgbase.Maintainer
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
    elif request.user.has_credential(creds.PKGBASE_DISOWN):
        # Otherwise, the request user performing this disownage is a
        # Trusted User and we treat it like a standard orphan request.
        notifs += handle_request(request, ORPHAN_ID, pkgbase)
        with db.begin():
            pkgbase.Maintainer = None
            db.delete_all(pkgbase.comaintainers)

    util.apply_all(notifs, lambda n: n.send())


def pkgbase_adopt_instance(request: Request, pkgbase: PackageBase) -> None:
    with db.begin():
        pkgbase.Maintainer = request.user

    notif = notify.AdoptNotification(request.user.ID, pkgbase.ID)
    notif.send()


def pkgbase_delete_instance(request: Request, pkgbase: PackageBase,
                            comments: str = str()) \
        -> List[notify.Notification]:
    notifs = handle_request(request, DELETION_ID, pkgbase) + [
        notify.DeleteNotification(request.user.ID, pkgbase.ID)
    ]

    with db.begin():
        update_closure_comment(pkgbase, DELETION_ID, comments)
        db.delete(pkgbase)

    return notifs


def pkgbase_merge_instance(request: Request, pkgbase: PackageBase,
                           target: PackageBase, comments: str = str()) -> None:
    pkgbasename = str(pkgbase.Name)

    # Create notifications.
    notifs = handle_request(request, MERGE_ID, pkgbase, target)

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

    # Log this out for accountability purposes.
    logger.info(f"Trusted User '{request.user.Username}' merged "
                f"'{pkgbasename}' into '{target.Name}'.")

    # Send notifications.
    util.apply_all(notifs, lambda n: n.send())
