from http import HTTPStatus

from fastapi import APIRouter, Form, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import case

from aurweb import db, defaults, time, util
from aurweb.auth import creds, requires_auth
from aurweb.models import PackageRequest, User
from aurweb.models.package_request import PENDING_ID, REJECTED_ID
from aurweb.requests.util import get_pkgreq_by_id
from aurweb.scripts import notify
from aurweb.templates import make_context, render_template

router = APIRouter()


@router.get("/requests")
@requires_auth
async def requests(request: Request,
                   O: int = Query(default=defaults.O),
                   PP: int = Query(default=defaults.PP)):
    context = make_context(request, "Requests")

    context["q"] = dict(request.query_params)

    O, PP = util.sanitize_params(O, PP)
    context["O"] = O
    context["PP"] = PP

    # A PackageRequest query, with left inner joined User and RequestType.
    query = db.query(PackageRequest).join(
        User, User.ID == PackageRequest.UsersID)

    # If the request user is not elevated (TU or Dev), then
    # filter PackageRequests which are owned by the request user.
    if not request.user.is_elevated():
        query = query.filter(PackageRequest.UsersID == request.user.ID)

    context["total"] = query.count()
    context["results"] = query.order_by(
        # Order primarily by the Status column being PENDING_ID,
        # and secondarily by RequestTS; both in descending order.
        case([(PackageRequest.Status == PENDING_ID, 1)], else_=0).desc(),
        PackageRequest.RequestTS.desc()
    ).limit(PP).offset(O).all()

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


@router.post("/requests/{id}/close")
@requires_auth
async def request_close_post(request: Request, id: int,
                             comments: str = Form(default=str())):
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
        request.user.ID, pkgreq.ID, pkgreq.status_display())
    notify_.send()

    return RedirectResponse("/requests", status_code=HTTPStatus.SEE_OTHER)
