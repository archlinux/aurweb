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
from aurweb.models.account_type import (
    PACKAGE_MAINTAINER_AND_DEV_ID,
    PACKAGE_MAINTAINER_ID,
)
from aurweb.templates import make_context, make_variable_context, render_template

router = APIRouter()
logger = aur_logging.get_logger(__name__)

# Some PM route specific constants.
ITEMS_PER_PAGE = 10  # Paged table size.
MAX_AGENDA_LENGTH = 75  # Agenda table column length.

ADDVOTE_SPECIFICS = {
    # This dict stores a vote duration and quorum for a proposal.
    # When a proposal is added, duration is added to the current
    # timestamp.
    # "addvote_type": (duration, quorum)
    "add_pm": (7 * 24 * 60 * 60, 0.66),
    "remove_pm": (7 * 24 * 60 * 60, 0.75),
    "remove_inactive_pm": (5 * 24 * 60 * 60, 0.66),
    "bylaws": (7 * 24 * 60 * 60, 0.75),
}


def populate_package_maintainer_counts(context: dict[str, Any]) -> None:
    pm_query = db.query(User).filter(
        or_(
            User.AccountTypeID == PACKAGE_MAINTAINER_ID,
            User.AccountTypeID == PACKAGE_MAINTAINER_AND_DEV_ID,
        )
    )
    context["package_maintainer_count"] = pm_query.count()

    # In case any records have a None InactivityTS.
    active_pm_query = pm_query.filter(
        or_(User.InactivityTS.is_(None), User.InactivityTS == 0)
    )
    context["active_package_maintainer_count"] = active_pm_query.count()


@router.get("/package-maintainer")
@requires_auth
async def package_maintainer(
    request: Request,
    coff: int = 0,  # current offset
    cby: str = "desc",  # current by
    poff: int = 0,  # past offset
    pby: str = "desc",
):  # past by
    """Proposal listings."""

    if not request.user.has_credential(creds.PM_LIST_VOTES):
        return RedirectResponse("/", status_code=HTTPStatus.SEE_OTHER)

    context = make_context(request, "Package Maintainer")

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
        db.query(models.VoteInfo)
        .filter(models.VoteInfo.End > ts)
        .order_by(models.VoteInfo.Submitted.desc())
    )
    context["current_votes_count"] = current_votes.count()
    current_votes = current_votes.limit(pp).offset(current_off)
    context["current_votes"] = (
        reversed(current_votes.all()) if current_by == "asc" else current_votes.all()
    )
    context["current_off"] = current_off

    past_votes = (
        db.query(models.VoteInfo)
        .filter(models.VoteInfo.End <= ts)
        .order_by(models.VoteInfo.Submitted.desc())
    )
    context["past_votes_count"] = past_votes.count()
    past_votes = past_votes.limit(pp).offset(past_off)
    context["past_votes"] = (
        reversed(past_votes.all()) if past_by == "asc" else past_votes.all()
    )
    context["past_off"] = past_off

    last_vote = func.max(models.Vote.VoteID).label("LastVote")
    last_votes_by_pm = (
        db.query(models.Vote)
        .join(models.User)
        .join(models.VoteInfo, models.VoteInfo.ID == models.Vote.VoteID)
        .filter(
            and_(
                models.Vote.VoteID == models.VoteInfo.ID,
                models.User.ID == models.Vote.UserID,
                models.VoteInfo.End < ts,
                or_(models.User.AccountTypeID == 2, models.User.AccountTypeID == 4),
            )
        )
        .with_entities(models.Vote.UserID, last_vote, models.User.Username)
        .group_by(models.Vote.UserID, models.User.Username)
        .order_by(last_vote.desc(), models.User.Username.asc())
    )
    context["last_votes_by_pm"] = last_votes_by_pm.all()

    context["current_by_next"] = "asc" if current_by == "desc" else "desc"
    context["past_by_next"] = "asc" if past_by == "desc" else "desc"

    populate_package_maintainer_counts(context)

    context["q"] = {
        "coff": current_off,
        "cby": current_by,
        "poff": past_off,
        "pby": past_by,
    }

    return render_template(request, "package-maintainer/index.html", context)


def render_proposal(
    request: Request,
    context: dict,
    proposal: int,
    voteinfo: models.VoteInfo,
    voters: typing.Iterable[models.User],
    vote: models.Vote,
    status_code: HTTPStatus = HTTPStatus.OK,
):
    """Render a single PM proposal."""
    context["proposal"] = proposal
    context["voteinfo"] = voteinfo
    context["voters"] = voters.all()

    total = voteinfo.total_votes()
    participation = (total / voteinfo.ActiveUsers) if voteinfo.ActiveUsers else 0
    context["participation"] = participation

    accepted = (voteinfo.Yes > voteinfo.ActiveUsers / 2) or (
        participation > voteinfo.Quorum and voteinfo.Yes > voteinfo.No
    )
    context["accepted"] = accepted

    can_vote = voters.filter(models.Vote.User == request.user).first() is None
    context["can_vote"] = can_vote

    if not voteinfo.is_running():
        context["error"] = "Voting is closed for this proposal."

    context["vote"] = vote
    context["has_voted"] = vote is not None

    return render_template(
        request, "package-maintainer/show.html", context, status_code=status_code
    )


@router.get("/package-maintainer/{proposal}")
@requires_auth
async def package_maintainer_proposal(request: Request, proposal: int):
    if not request.user.has_credential(creds.PM_LIST_VOTES):
        return RedirectResponse("/package-maintainer", status_code=HTTPStatus.SEE_OTHER)

    context = await make_variable_context(request, "Package Maintainer")
    proposal = int(proposal)

    voteinfo = db.query(models.VoteInfo).filter(models.VoteInfo.ID == proposal).first()
    if not voteinfo:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND)

    voters = (
        db.query(models.User)
        .join(models.Vote)
        .filter(models.Vote.VoteID == voteinfo.ID)
    )
    vote = (
        db.query(models.Vote)
        .filter(
            and_(
                models.Vote.UserID == request.user.ID,
                models.Vote.VoteID == voteinfo.ID,
            )
        )
        .first()
    )
    if not request.user.has_credential(creds.PM_VOTE):
        context["error"] = "Only Package Maintainers are allowed to vote."
    if voteinfo.User == request.user.Username:
        context["error"] = "You cannot vote in an proposal about you."
    elif vote is not None:
        context["error"] = "You've already voted for this proposal."

    context["vote"] = vote
    return render_proposal(request, context, proposal, voteinfo, voters, vote)


@db.async_retry_deadlock
@router.post("/package-maintainer/{proposal}")
@handle_form_exceptions
@requires_auth
async def package_maintainer_proposal_post(
    request: Request, proposal: int, decision: str = Form(...)
):
    if not request.user.has_credential(creds.PM_LIST_VOTES):
        return RedirectResponse("/package-maintainer", status_code=HTTPStatus.SEE_OTHER)

    context = await make_variable_context(request, "Package Maintainer")
    proposal = int(proposal)  # Make sure it's an int.

    voteinfo = db.query(models.VoteInfo).filter(models.VoteInfo.ID == proposal).first()
    if not voteinfo:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND)

    voters = (
        db.query(models.User)
        .join(models.Vote)
        .filter(models.Vote.VoteID == voteinfo.ID)
    )
    vote = (
        db.query(models.Vote)
        .filter(
            and_(
                models.Vote.UserID == request.user.ID,
                models.Vote.VoteID == voteinfo.ID,
            )
        )
        .first()
    )

    status_code = HTTPStatus.OK
    if not request.user.has_credential(creds.PM_VOTE):
        context["error"] = "Only Package Maintainers are allowed to vote."
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

        vote = db.create(models.Vote, User=request.user, VoteInfo=voteinfo)

    context["error"] = "You've already voted for this proposal."
    return render_proposal(request, context, proposal, voteinfo, voters, vote)


@router.get("/addvote")
@requires_auth
async def package_maintainer_addvote(
    request: Request, user: str = str(), type: str = "add_pm", agenda: str = str()
):
    if not request.user.has_credential(creds.PM_ADD_VOTE):
        return RedirectResponse("/package-maintainer", status_code=HTTPStatus.SEE_OTHER)

    context = await make_variable_context(request, "Add Proposal")

    if type not in ADDVOTE_SPECIFICS:
        context["error"] = "Invalid type."
        type = "add_pm"  # Default it.

    context["user"] = user
    context["type"] = type
    context["agenda"] = agenda

    return render_template(request, "addvote.html", context)


@db.async_retry_deadlock
@router.post("/addvote")
@handle_form_exceptions
@requires_auth
async def package_maintainer_addvote_post(
    request: Request,
    user: str = Form(default=str()),
    type: str = Form(default=str()),
    agenda: str = Form(default=str()),
):
    if not request.user.has_credential(creds.PM_ADD_VOTE):
        return RedirectResponse("/package-maintainer", status_code=HTTPStatus.SEE_OTHER)

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
            db.query(models.VoteInfo)
            .filter(and_(models.VoteInfo.User == user, models.VoteInfo.End > utcnow))
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
        context["type"] = type = "add_pm"  # Default for rendering.
        return render_addvote(context, HTTPStatus.BAD_REQUEST)

    if not agenda:
        context["error"] = "Proposal cannot be empty."
        return render_addvote(context, HTTPStatus.BAD_REQUEST)

    # Gather some mapped constants and the current timestamp.
    duration, quorum = ADDVOTE_SPECIFICS.get(type)
    timestamp = time.utcnow()

    # Active PM types we filter for.
    types = {PACKAGE_MAINTAINER_ID, PACKAGE_MAINTAINER_AND_DEV_ID}

    # Create a new VoteInfo (proposal)!
    with db.begin():
        active_pms = (
            db.query(User)
            .filter(
                and_(
                    ~User.Suspended,
                    User.InactivityTS.isnot(None),
                    User.AccountTypeID.in_(types),
                )
            )
            .count()
        )
        voteinfo = db.create(
            models.VoteInfo,
            User=user,
            Agenda=html.escape(agenda),
            Submitted=timestamp,
            End=(timestamp + duration),
            Quorum=quorum,
            ActiveUsers=active_pms,
            Submitter=request.user,
        )

    # Redirect to the new proposal.
    endpoint = f"/package-maintainer/{voteinfo.ID}"
    return RedirectResponse(endpoint, status_code=HTTPStatus.SEE_OTHER)
