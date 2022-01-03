from datetime import datetime
from typing import List, Optional, Set

from fastapi import Request
from sqlalchemy import and_, orm

from aurweb import config, db, l10n, util
from aurweb.exceptions import InvariantError
from aurweb.models import PackageBase, PackageRequest, User
from aurweb.models.package_request import ACCEPTED_ID, PENDING_ID, REJECTED_ID
from aurweb.models.request_type import DELETION, DELETION_ID, MERGE, MERGE_ID, ORPHAN, ORPHAN_ID
from aurweb.scripts import notify


class ClosureFactory:
    """ A factory class used to autogenerate closure comments. """

    REQTYPE_NAMES = {
        DELETION_ID: DELETION,
        MERGE_ID: MERGE,
        ORPHAN_ID: ORPHAN
    }

    def _deletion_closure(self, requester: User,
                          pkgbase: PackageBase,
                          target: PackageBase = None):
        return (f"[Autogenerated] Accepted deletion for {pkgbase.Name}.")

    def _merge_closure(self, requester: User,
                       pkgbase: PackageBase,
                       target: PackageBase = None):
        return (f"[Autogenerated] Accepted merge for {pkgbase.Name} "
                "into {target.Name}.")

    def _orphan_closure(self, requester: User,
                        pkgbase: PackageBase,
                        target: PackageBase = None):
        return (f"[Autogenerated] Accepted orphan for {pkgbase.Name}.")

    def _rejected_merge_closure(self, requester: User,
                                pkgbase: PackageBase,
                                target: PackageBase = None):
        return (f"[Autogenerated] Another request to merge {pkgbase.Name} "
                f"into {target.Name} has rendered this request invalid.")

    def get_closure(self, reqtype_id: int,
                    requester: User,
                    pkgbase: PackageBase,
                    target: PackageBase = None,
                    status: int = ACCEPTED_ID) -> str:
        """
        Return a closure comment handled by this class.

        :param reqtype_id: RequestType.ID
        :param requester: User who is closing a request
        :param pkgbase: PackageBase instance related to the request
        :param target: Merge request target PackageBase instance
        :param status: PackageRequest.Status
        """
        reqtype = ClosureFactory.REQTYPE_NAMES.get(reqtype_id)

        partial = str()
        if status == REJECTED_ID:
            partial = "_rejected"

        try:
            handler = getattr(self, f"{partial}_{reqtype}_closure")
        except AttributeError:
            raise NotImplementedError("Unsupported 'reqtype_id' value.")
        return handler(requester, pkgbase, target)


def update_closure_comment(pkgbase: PackageBase, reqtype_id: int,
                           comments: str, target: PackageBase = None) -> None:
    """
    Update all pending requests related to `pkgbase` with a closure comment.

    In order to persist closure comments through `handle_request`'s
    algorithm, we must set `PackageRequest.ClosureComment` before calling
    it. This function can be used to update the closure comment of all
    package requests related to `pkgbase` and `reqtype_id`.

    If an empty `comments` string is provided, we no-op out of this.

    :param pkgbase: PackageBase instance
    :param reqtype_id: RequestType.ID
    :param comments: PackageRequest.ClosureComment to update to
    :param target: Merge request target PackageBase instance
    """
    if not comments:
        return

    query = pkgbase.requests.filter(
        and_(PackageRequest.ReqTypeID == reqtype_id,
             PackageRequest.Status == PENDING_ID))
    if reqtype_id == MERGE_ID:
        query = query.filter(PackageRequest.MergeBaseName == target.Name)

    for pkgreq in query:
        pkgreq.ClosureComment = comments


def verify_orphan_request(user: User, pkgbase: PackageBase):
    """ Verify that an undue orphan request exists in `requests`. """
    requests = pkgbase.requests.filter(
        PackageRequest.ReqTypeID == ORPHAN_ID)
    for pkgreq in requests:
        idle_time = config.getint("options", "request_idle_time")
        time_delta = int(datetime.utcnow().timestamp()) - pkgreq.RequestTS
        is_due = pkgreq.Status == PENDING_ID and time_delta > idle_time
        if is_due:
            # If the requester is the pkgbase maintainer or the
            # request is already due, we're good to go: return True.
            return True

    return False


def close_pkgreq(pkgreq: PackageRequest, closer: User,
                 pkgbase: PackageBase, target: Optional[PackageBase],
                 status: int) -> None:
    """
    Close a package request with `pkgreq`.Status == `status`.

    :param pkgreq: PackageRequest instance
    :param closer: `pkgreq`.Closer User instance to update to
    :param pkgbase: PackageBase instance which `pkgreq` is about
    :param target: Optional PackageBase instance to merge into
    :param status: `pkgreq`.Status value to update to
    """
    now = int(datetime.utcnow().timestamp())
    pkgreq.Status = status
    pkgreq.Closer = closer
    pkgreq.ClosureComment = (
        pkgreq.ClosureComment or ClosureFactory().get_closure(
            pkgreq.ReqTypeID, closer, pkgbase, target, status)
    )
    pkgreq.ClosedTS = now


def handle_request(request: Request, reqtype_id: int,
                   pkgbase: PackageBase,
                   target: PackageBase = None) -> List[notify.Notification]:
    """
    Handle package requests before performing an action.

    The actions we're interested in are disown (orphan), delete and
    merge. There is now an automated request generation and closure
    notification when a privileged user performs one of these actions
    without a pre-existing request. They all commit changes to the
    database, and thus before calling, state should be verified to
    avoid leaked database records regarding these requests.

    Otherwise, we accept and reject requests based on their state
    and send out the relevent notifications.

    :param requester: User who needs this a `pkgbase` request handled
    :param reqtype_id: RequestType.ID
    :param pkgbase: PackageBase which the request is about
    :param target: Optional target to merge into
    """
    notifs: List[notify.Notification] = []

    # If it's an orphan request, perform further verification
    # regarding existing requests.
    if reqtype_id == ORPHAN_ID:
        if not verify_orphan_request(request.user, pkgbase):
            _ = l10n.get_translator_for_request(request)
            raise InvariantError(_(
                "No due existing orphan requests to accept for %s."
            ) % pkgbase.Name)

    # Produce a base query for requests related to `pkgbase`, based
    # on ReqTypeID matching `reqtype_id`, pending status and a correct
    # PackagBaseName column.
    query: orm.Query = pkgbase.requests.filter(
        and_(PackageRequest.ReqTypeID == reqtype_id,
             PackageRequest.Status == PENDING_ID,
             PackageRequest.PackageBaseName == pkgbase.Name))

    # Build a query for records we should accept. For merge requests,
    # this is specific to a matching MergeBaseName. For others, this
    # just ends up becoming `query`.
    accept_query: orm.Query = query
    if target:
        # If a `target` was supplied, filter by MergeBaseName
        accept_query = query.filter(
            PackageRequest.MergeBaseName == target.Name)

    # Build an accept list out of `accept_query`.
    to_accept: List[PackageRequest] = accept_query.all()
    accepted_ids: Set[int] = set(p.ID for p in to_accept)

    # Build a reject list out of `query` filtered by IDs not found
    # in `to_accept`. That is, unmatched records of the same base
    # query properties.
    to_reject: List[PackageRequest] = query.filter(
        ~PackageRequest.ID.in_(accepted_ids)
    ).all()

    # If we have no requests to accept, create a new one.
    # This is done to increase tracking of actions occurring
    # through the website.
    if not to_accept:
        with db.begin():
            pkgreq = db.create(PackageRequest,
                               ReqTypeID=reqtype_id,
                               User=request.user,
                               PackageBase=pkgbase,
                               PackageBaseName=pkgbase.Name,
                               Comments="Autogenerated by aurweb.",
                               ClosureComment=str())

            # If it's a merge request, set MergeBaseName to `target`.Name.
            if pkgreq.ReqTypeID == MERGE_ID:
                pkgreq.MergeBaseName = target.Name

            # Add the new request to `to_accept` and allow standard
            # flow to continue afterward.
            to_accept.append(pkgreq)

    # Update requests with their new status and closures.
    with db.begin():
        util.apply_all(to_accept, lambda p: close_pkgreq(
            p, request.user, pkgbase, target, ACCEPTED_ID))
        util.apply_all(to_reject, lambda p: close_pkgreq(
            p, request.user, pkgbase, target, REJECTED_ID))

    # Create RequestCloseNotifications for all requests involved.
    for pkgreq in (to_accept + to_reject):
        notif = notify.RequestCloseNotification(
            request.user.ID, pkgreq.ID, pkgreq.status_display())
        notifs.append(notif)

    # Return notifications to the caller for sending.
    return notifs