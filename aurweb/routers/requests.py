from http import HTTPStatus

from fastapi import APIRouter, Form, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import case, orm

from aurweb import db, defaults, time, util
from aurweb.auth import creds, requires_auth
from aurweb.exceptions import handle_form_exceptions
from aurweb.models import PackageBase, PackageRequest, User
from aurweb.models.package_request import (
    ACCEPTED_ID,
    CLOSED_ID,
    PENDING_ID,
    REJECTED_ID,
)
from aurweb.requests.util import get_pkgreq_by_id
from aurweb.scripts import notify
from aurweb.templates import make_context, render_template

FILTER_PARAMS = {
    "filter_pending",
    "filter_closed",
    "filter_accepted",
    "filter_rejected",
    "filter_maintainers_requests",
}

router = APIRouter()


@router.get("/requests")
@requires_auth
async def requests(
    request: Request,
    O: int = Query(default=defaults.O),
    PP: int = Query(default=defaults.PP),
    filter_pending: bool = False,
    filter_closed: bool = False,
    filter_accepted: bool = False,
    filter_rejected: bool = False,
    filter_maintainer_requests: bool = False,
):
    context = make_context(request, "Requests")

    context["q"] = dict(request.query_params)

    if not dict(request.query_params).keys() & FILTER_PARAMS:
        filter_pending = True

    O, PP = util.sanitize_params(str(O), str(PP))
    context["O"] = O
    context["PP"] = PP
    context["filter_pending"] = filter_pending
    context["filter_closed"] = filter_closed
    context["filter_accepted"] = filter_accepted
    context["filter_rejected"] = filter_rejected
    context["filter_maintainer_requests"] = filter_maintainer_requests

    Maintainer = orm.aliased(User)
    # A PackageRequest query
    query = (
        db.query(PackageRequest)
        .join(PackageBase)
        .join(User, PackageRequest.UsersID == User.ID, isouter=True)
        .join(Maintainer, PackageBase.MaintainerUID == Maintainer.ID, isouter=True)
    )
    # query = db.query(PackageRequest).join(User)

    # Requests statistics
    context["total_requests"] = query.count()
    pending_count = 0 + query.filter(PackageRequest.Status == PENDING_ID).count()
    context["pending_requests"] = pending_count
    closed_count = 0 + query.filter(PackageRequest.Status == CLOSED_ID).count()
    context["closed_requests"] = closed_count
    accepted_count = 0 + query.filter(PackageRequest.Status == ACCEPTED_ID).count()
    context["accepted_requests"] = accepted_count
    rejected_count = 0 + query.filter(PackageRequest.Status == REJECTED_ID).count()
    context["rejected_requests"] = rejected_count

    # Apply filters
    in_filters = []
    if filter_pending:
        in_filters.append(PENDING_ID)
    if filter_closed:
        in_filters.append(CLOSED_ID)
    if filter_accepted:
        in_filters.append(ACCEPTED_ID)
    if filter_rejected:
        in_filters.append(REJECTED_ID)
    filtered = query.filter(PackageRequest.Status.in_(in_filters))
    # Additionally filter for requests made from package maintainer
    if filter_maintainer_requests:
        filtered = filtered.filter(PackageRequest.UsersID == PackageBase.MaintainerUID)
    # If the request user is not elevated (TU or Dev), then
    # filter PackageRequests which are owned by the request user.
    if not request.user.is_elevated():
        filtered = filtered.filter(PackageRequest.UsersID == request.user.ID)

    context["total"] = filtered.count()
    context["results"] = (
        filtered.order_by(
            # Order primarily by the Status column being PENDING_ID,
            # and secondarily by RequestTS; both in descending order.
            case([(PackageRequest.Status == PENDING_ID, 1)], else_=0).desc(),
            PackageRequest.RequestTS.desc(),
        )
        .limit(PP)
        .offset(O)
        .all()
    )
    return render_template(request, "requests.html", context)


@router.get("/requests/{id}/close")
@requires_auth
async def request_close(request: Request, id: int):

    pkgreq = get_pkgreq_by_id(id)
    if not request.user.is_elevated() and request.user != pkgreq.User:
        # Request user doesn't have permission here: redirect to '/'.
        return RedirectResponse("/", status_code=HTTPStatus.SEE_OTHER)

    context = make_context(request, "Close Request")
    context["pkgreq"] = pkgreq
    return render_template(request, "requests/close.html", context)


@db.async_retry_deadlock
@router.post("/requests/{id}/close")
@handle_form_exceptions
@requires_auth
async def request_close_post(
    request: Request, id: int, comments: str = Form(default=str())
):
    pkgreq = get_pkgreq_by_id(id)

    # `pkgreq`.User can close their own request.
    approved = [pkgreq.User]
    if not request.user.has_credential(creds.PKGREQ_CLOSE, approved=approved):
        # Request user doesn't have permission here: redirect to '/'.
        return RedirectResponse("/", status_code=HTTPStatus.SEE_OTHER)

    context = make_context(request, "Close Request")
    context["pkgreq"] = pkgreq

    now = time.utcnow()
    with db.begin():
        pkgreq.Closer = request.user
        pkgreq.ClosureComment = comments
        pkgreq.ClosedTS = now
        pkgreq.Status = REJECTED_ID

    notify_ = notify.RequestCloseNotification(
        request.user.ID, pkgreq.ID, pkgreq.status_display()
    )
    notify_.send()

    return RedirectResponse("/requests", status_code=HTTPStatus.SEE_OTHER)
