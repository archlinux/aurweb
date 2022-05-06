import html
import typing
from http import HTTPStatus
from typing import Any

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import RedirectResponse, Response
from sqlalchemy import and_, func, or_

from aurweb import aur_logging, db, l10n, models, time
from aurweb.auth import creds, requires_auth
from aurweb.exceptions import handle_form_exceptions
from aurweb.models import User
from aurweb.models.account_type import TRUSTED_USER_AND_DEV_ID, TRUSTED_USER_ID
from aurweb.templates import make_context, make_variable_context, render_template

router = APIRouter()
logger = aur_logging.get_logger(__name__)

# Some TU route specific constants.
ITEMS_PER_PAGE = 10  # Paged table size.
MAX_AGENDA_LENGTH = 75  # Agenda table column length.

ADDVOTE_SPECIFICS = {
    # This dict stores a vote duration and quorum for a proposal.
    # When a proposal is added, duration is added to the current
    # timestamp.
    # "addvote_type": (duration, quorum)
    "add_tu": (7 * 24 * 60 * 60, 0.66),
    "remove_tu": (7 * 24 * 60 * 60, 0.75),
    "remove_inactive_tu": (5 * 24 * 60 * 60, 0.66),
    "bylaws": (7 * 24 * 60 * 60, 0.75),
}


def populate_trusted_user_counts(context: dict[str, Any]) -> None:
    tu_query = db.query(User).filter(
        or_(
            User.AccountTypeID == TRUSTED_USER_ID,
            User.AccountTypeID == TRUSTED_USER_AND_DEV_ID,
        )
    )
    context["trusted_user_count"] = tu_query.count()

    # In case any records have a None InactivityTS.
    active_tu_query = tu_query.filter(
        or_(User.InactivityTS.is_(None), User.InactivityTS == 0)
    )
    context["active_trusted_user_count"] = active_tu_query.count()


@router.get("/tu")
@requires_auth
async def trusted_user(
    request: Request,
    coff: int = 0,  # current offset
    cby: str = "desc",  # current by
    poff: int = 0,  # past offset
    pby: str = "desc",
):  # past by
    """Proposal listings."""

    if not request.user.has_credential(creds.TU_LIST_VOTES):
        return RedirectResponse("/", status_code=HTTPStatus.SEE_OTHER)

    context = make_context(request, "Trusted User")

    current_by, past_by = cby, pby
    current_off, past_off = coff, poff

    context["pp"] = pp = ITEMS_PER_PAGE
    context["prev_len"] = MAX_AGENDA_LENGTH

    ts = time.utcnow()

    if current_by not in {"asc", "desc"}:
        # If a malicious by was given, default to desc.
        current_by = "desc"
    context["current_by"] = current_by

    if past_by not in {"asc", "desc"}:
        # If a malicious by was given, default to desc.
        past_by = "desc"
    context["past_by"] = past_by

    current_votes = (
        db.query(models.TUVoteInfo)
        .filter(models.TUVoteInfo.End > ts)
        .order_by(models.TUVoteInfo.Submitted.desc())
    )
    context["current_votes_count"] = current_votes.count()
    current_votes = current_votes.limit(pp).offset(current_off)
    context["current_votes"] = (
        reversed(current_votes.all()) if current_by == "asc" else current_votes.all()
    )
    context["current_off"] = current_off

    past_votes = (
        db.query(models.TUVoteInfo)
        .filter(models.TUVoteInfo.End <= ts)
        .order_by(models.TUVoteInfo.Submitted.desc())
    )
    context["past_votes_count"] = past_votes.count()
    past_votes = past_votes.limit(pp).offset(past_off)
    context["past_votes"] = (
        reversed(past_votes.all()) if past_by == "asc" else past_votes.all()
    )
    context["past_off"] = past_off

    last_vote = func.max(models.TUVote.VoteID).label("LastVote")
    last_votes_by_tu = (
        db.query(models.TUVote)
        .join(models.User)
        .join(models.TUVoteInfo, models.TUVoteInfo.ID == models.TUVote.VoteID)
        .filter(
            and_(
                models.TUVote.VoteID == models.TUVoteInfo.ID,
                models.User.ID == models.TUVote.UserID,
                models.TUVoteInfo.End < ts,
                or_(models.User.AccountTypeID == 2, models.User.AccountTypeID == 4),
            )
        )
        .with_entities(models.TUVote.UserID, last_vote, models.User.Username)
        .group_by(models.TUVote.UserID)
        .order_by(last_vote.desc(), models.User.Username.asc())
    )
    context["last_votes_by_tu"] = last_votes_by_tu.all()

    context["current_by_next"] = "asc" if current_by == "desc" else "desc"
    context["past_by_next"] = "asc" if past_by == "desc" else "desc"

    populate_trusted_user_counts(context)

    context["q"] = {
        "coff": current_off,
        "cby": current_by,
        "poff": past_off,
        "pby": past_by,
    }

    return render_template(request, "tu/index.html", context)


def render_proposal(
    request: Request,
    context: dict,
    proposal: int,
    voteinfo: models.TUVoteInfo,
    voters: typing.Iterable[models.User],
    vote: models.TUVote,
    status_code: HTTPStatus = HTTPStatus.OK,
):
    """Render a single TU proposal."""
    context["proposal"] = proposal
    context["voteinfo"] = voteinfo
    context["voters"] = voters.all()

    total = voteinfo.total_votes()
    participation = (total / voteinfo.ActiveTUs) if voteinfo.ActiveTUs else 0
    context["participation"] = participation

    accepted = (voteinfo.Yes > voteinfo.ActiveTUs / 2) or (
        participation > voteinfo.Quorum and voteinfo.Yes > voteinfo.No
    )
    context["accepted"] = accepted

    can_vote = voters.filter(models.TUVote.User == request.user).first() is None
    context["can_vote"] = can_vote

    if not voteinfo.is_running():
        context["error"] = "Voting is closed for this proposal."

    context["vote"] = vote
    context["has_voted"] = vote is not None

    return render_template(request, "tu/show.html", context, status_code=status_code)


@router.get("/tu/{proposal}")
@requires_auth
async def trusted_user_proposal(request: Request, proposal: int):
    if not request.user.has_credential(creds.TU_LIST_VOTES):
        return RedirectResponse("/tu", status_code=HTTPStatus.SEE_OTHER)

    context = await make_variable_context(request, "Trusted User")
    proposal = int(proposal)

    voteinfo = (
        db.query(models.TUVoteInfo).filter(models.TUVoteInfo.ID == proposal).first()
    )
    if not voteinfo:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND)

    voters = (
        db.query(models.User)
        .join(models.TUVote)
        .filter(models.TUVote.VoteID == voteinfo.ID)
    )
    vote = (
        db.query(models.TUVote)
        .filter(
            and_(
                models.TUVote.UserID == request.user.ID,
                models.TUVote.VoteID == voteinfo.ID,
            )
        )
        .first()
    )
    if not request.user.has_credential(creds.TU_VOTE):
        context["error"] = "Only Trusted Users are allowed to vote."
    if voteinfo.User == request.user.Username:
        context["error"] = "You cannot vote in an proposal about you."
    elif vote is not None:
        context["error"] = "You've already voted for this proposal."

    context["vote"] = vote
    return render_proposal(request, context, proposal, voteinfo, voters, vote)


@db.async_retry_deadlock
@router.post("/tu/{proposal}")
@handle_form_exceptions
@requires_auth
async def trusted_user_proposal_post(
    request: Request, proposal: int, decision: str = Form(...)
):
    if not request.user.has_credential(creds.TU_LIST_VOTES):
        return RedirectResponse("/tu", status_code=HTTPStatus.SEE_OTHER)

    context = await make_variable_context(request, "Trusted User")
    proposal = int(proposal)  # Make sure it's an int.

    voteinfo = (
        db.query(models.TUVoteInfo).filter(models.TUVoteInfo.ID == proposal).first()
    )
    if not voteinfo:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND)

    voters = (
        db.query(models.User)
        .join(models.TUVote)
        .filter(models.TUVote.VoteID == voteinfo.ID)
    )
    vote = (
        db.query(models.TUVote)
        .filter(
            and_(
                models.TUVote.UserID == request.user.ID,
                models.TUVote.VoteID == voteinfo.ID,
            )
        )
        .first()
    )

    status_code = HTTPStatus.OK
    if not request.user.has_credential(creds.TU_VOTE):
        context["error"] = "Only Trusted Users are allowed to vote."
        status_code = HTTPStatus.UNAUTHORIZED
    elif voteinfo.User == request.user.Username:
        context["error"] = "You cannot vote in an proposal about you."
        status_code = HTTPStatus.BAD_REQUEST
    elif vote is not None:
        context["error"] = "You've already voted for this proposal."
        status_code = HTTPStatus.BAD_REQUEST

    if status_code != HTTPStatus.OK:
        return render_proposal(
            request, context, proposal, voteinfo, voters, vote, status_code=status_code
        )

    with db.begin():
        if decision in {"Yes", "No", "Abstain"}:
            # Increment whichever decision was given to us.
            setattr(voteinfo, decision, getattr(voteinfo, decision) + 1)
        else:
            return Response(
                "Invalid 'decision' value.", status_code=HTTPStatus.BAD_REQUEST
            )

        vote = db.create(models.TUVote, User=request.user, VoteInfo=voteinfo)

    context["error"] = "You've already voted for this proposal."
    return render_proposal(request, context, proposal, voteinfo, voters, vote)


@router.get("/addvote")
@requires_auth
async def trusted_user_addvote(
    request: Request, user: str = str(), type: str = "add_tu", agenda: str = str()
):
    if not request.user.has_credential(creds.TU_ADD_VOTE):
        return RedirectResponse("/tu", status_code=HTTPStatus.SEE_OTHER)

    context = await make_variable_context(request, "Add Proposal")

    if type not in ADDVOTE_SPECIFICS:
        context["error"] = "Invalid type."
        type = "add_tu"  # Default it.

    context["user"] = user
    context["type"] = type
    context["agenda"] = agenda

    return render_template(request, "addvote.html", context)


@db.async_retry_deadlock
@router.post("/addvote")
@handle_form_exceptions
@requires_auth
async def trusted_user_addvote_post(
    request: Request,
    user: str = Form(default=str()),
    type: str = Form(default=str()),
    agenda: str = Form(default=str()),
):
    if not request.user.has_credential(creds.TU_ADD_VOTE):
        return RedirectResponse("/tu", status_code=HTTPStatus.SEE_OTHER)

    # Build a context.
    context = await make_variable_context(request, "Add Proposal")

    context["type"] = type
    context["user"] = user
    context["agenda"] = agenda

    def render_addvote(context, status_code):
        """Simplify render_template a bit for this test."""
        return render_template(request, "addvote.html", context, status_code)

    # Alright, get some database records, if we can.
    if type != "bylaws":
        user_record = db.query(models.User).filter(models.User.Username == user).first()
        if user_record is None:
            context["error"] = "Username does not exist."
            return render_addvote(context, HTTPStatus.NOT_FOUND)

        utcnow = time.utcnow()
        voteinfo = (
            db.query(models.TUVoteInfo)
            .filter(
                and_(models.TUVoteInfo.User == user, models.TUVoteInfo.End > utcnow)
            )
            .count()
        )
        if voteinfo:
            _ = l10n.get_translator_for_request(request)
            context["error"] = _("%s already has proposal running for them.") % (
                html.escape(user),
            )
            return render_addvote(context, HTTPStatus.BAD_REQUEST)

    if type not in ADDVOTE_SPECIFICS:
        context["error"] = "Invalid type."
        context["type"] = type = "add_tu"  # Default for rendering.
        return render_addvote(context, HTTPStatus.BAD_REQUEST)

    if not agenda:
        context["error"] = "Proposal cannot be empty."
        return render_addvote(context, HTTPStatus.BAD_REQUEST)

    # Gather some mapped constants and the current timestamp.
    duration, quorum = ADDVOTE_SPECIFICS.get(type)
    timestamp = time.utcnow()

    # Active TU types we filter for.
    types = {TRUSTED_USER_ID, TRUSTED_USER_AND_DEV_ID}

    # Create a new TUVoteInfo (proposal)!
    with db.begin():
        active_tus = (
            db.query(User)
            .filter(
                and_(
                    User.Suspended == 0,
                    User.InactivityTS.isnot(None),
                    User.AccountTypeID.in_(types),
                )
            )
            .count()
        )
        voteinfo = db.create(
            models.TUVoteInfo,
            User=user,
            Agenda=html.escape(agenda),
            Submitted=timestamp,
            End=(timestamp + duration),
            Quorum=quorum,
            ActiveTUs=active_tus,
            Submitter=request.user,
        )

    # Redirect to the new proposal.
    endpoint = f"/tu/{voteinfo.ID}"
    return RedirectResponse(endpoint, status_code=HTTPStatus.SEE_OTHER)
