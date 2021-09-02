import html
import logging
import re
import typing

from datetime import datetime
from http import HTTPStatus

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import RedirectResponse, Response
from sqlalchemy import and_, or_

from aurweb import db, l10n
from aurweb.auth import account_type_required, auth_required
from aurweb.models.account_type import DEVELOPER, TRUSTED_USER, TRUSTED_USER_AND_DEV
from aurweb.models.tu_vote import TUVote
from aurweb.models.tu_voteinfo import TUVoteInfo
from aurweb.models.user import User
from aurweb.templates import make_context, make_variable_context, render_template

router = APIRouter()
logger = logging.getLogger(__name__)

# Some TU route specific constants.
ITEMS_PER_PAGE = 10  # Paged table size.
MAX_AGENDA_LENGTH = 75  # Agenda table column length.

# A set of account types that will approve a user for TU actions.
REQUIRED_TYPES = {
    TRUSTED_USER,
    DEVELOPER,
    TRUSTED_USER_AND_DEV
}

ADDVOTE_SPECIFICS = {
    # This dict stores a vote duration and quorum for a proposal.
    # When a proposal is added, duration is added to the current
    # timestamp.
    # "addvote_type": (duration, quorum)
    "add_tu": (7 * 24 * 60 * 60, 0.66),
    "remove_tu": (7 * 24 * 60 * 60, 0.75),
    "remove_inactive_tu": (5 * 24 * 60 * 60, 0.66),
    "bylaws": (7 * 24 * 60 * 60, 0.75)
}


@router.get("/tu")
@auth_required(True, redirect="/")
@account_type_required(REQUIRED_TYPES)
async def trusted_user(request: Request,
                       coff: int = 0,  # current offset
                       cby: str = "desc",  # current by
                       poff: int = 0,  # past offset
                       pby: str = "desc"):  # past by
    context = make_context(request, "Trusted User")

    current_by, past_by = cby, pby
    current_off, past_off = coff, poff

    context["pp"] = pp = ITEMS_PER_PAGE
    context["prev_len"] = MAX_AGENDA_LENGTH

    ts = int(datetime.utcnow().timestamp())

    if current_by not in {"asc", "desc"}:
        # If a malicious by was given, default to desc.
        current_by = "desc"
    context["current_by"] = current_by

    if past_by not in {"asc", "desc"}:
        # If a malicious by was given, default to desc.
        past_by = "desc"
    context["past_by"] = past_by

    current_votes = db.query(TUVoteInfo, TUVoteInfo.End > ts).order_by(
        TUVoteInfo.Submitted.desc())
    context["current_votes_count"] = current_votes.count()
    current_votes = current_votes.limit(pp).offset(current_off)
    context["current_votes"] = reversed(current_votes.all()) \
        if current_by == "asc" else current_votes.all()
    context["current_off"] = current_off

    past_votes = db.query(TUVoteInfo, TUVoteInfo.End <= ts).order_by(
        TUVoteInfo.Submitted.desc())
    context["past_votes_count"] = past_votes.count()
    past_votes = past_votes.limit(pp).offset(past_off)
    context["past_votes"] = reversed(past_votes.all()) \
        if past_by == "asc" else past_votes.all()
    context["past_off"] = past_off

    # TODO
    # We order last votes by TUVote.VoteID and User.Username.
    # This is really bad. We should add a Created column to
    # TUVote of type Timestamp and order by that instead.
    last_votes_by_tu = db.query(TUVote).filter(
        and_(TUVote.VoteID == TUVoteInfo.ID,
             TUVoteInfo.End <= ts,
             TUVote.UserID == User.ID,
             or_(User.AccountTypeID == 2,
                 User.AccountTypeID == 4))
    ).group_by(User.ID).order_by(
        TUVote.VoteID.desc(), User.Username.asc())
    context["last_votes_by_tu"] = last_votes_by_tu.all()

    context["current_by_next"] = "asc" if current_by == "desc" else "desc"
    context["past_by_next"] = "asc" if past_by == "desc" else "desc"

    context["q"] = {
        "coff": current_off,
        "cby": current_by,
        "poff": past_off,
        "pby": past_by
    }

    return render_template(request, "tu/index.html", context)


def render_proposal(request: Request,
                    context: dict,
                    proposal: int,
                    voteinfo: TUVoteInfo,
                    voters: typing.Iterable[User],
                    vote: TUVote,
                    status_code: HTTPStatus = HTTPStatus.OK):
    """ Render a single TU proposal. """
    context["proposal"] = proposal
    context["voteinfo"] = voteinfo
    context["voters"] = voters.all()

    participation = voteinfo.ActiveTUs / voteinfo.total_votes() \
        if voteinfo.total_votes() else 0
    context["participation"] = participation

    accepted = (voteinfo.Yes > voteinfo.ActiveTUs / 2) or \
        (participation > voteinfo.Quorum and voteinfo.Yes > voteinfo.No)
    context["accepted"] = accepted

    can_vote = voters.filter(TUVote.User == request.user).first() is None
    context["can_vote"] = can_vote

    if not voteinfo.is_running():
        context["error"] = "Voting is closed for this proposal."

    context["vote"] = vote
    context["has_voted"] = vote is not None

    return render_template(request, "tu/show.html", context,
                           status_code=status_code)


@router.get("/tu/{proposal}")
@auth_required(True, redirect="/")
@account_type_required(REQUIRED_TYPES)
async def trusted_user_proposal(request: Request, proposal: int):
    context = await make_variable_context(request, "Trusted User")
    proposal = int(proposal)

    voteinfo = db.query(TUVoteInfo, TUVoteInfo.ID == proposal).first()
    if not voteinfo:
        raise HTTPException(status_code=int(HTTPStatus.NOT_FOUND))

    voters = db.query(User).join(TUVote).filter(TUVote.VoteID == voteinfo.ID)
    vote = db.query(TUVote, and_(TUVote.UserID == request.user.ID,
                                 TUVote.VoteID == voteinfo.ID)).first()

    if not request.user.is_trusted_user():
        context["error"] = "Only Trusted Users are allowed to vote."
    elif voteinfo.User == request.user.Username:
        context["error"] = "You cannot vote in an proposal about you."
    elif vote is not None:
        context["error"] = "You've already voted for this proposal."

    context["vote"] = vote
    return render_proposal(request, context, proposal, voteinfo, voters, vote)


@router.post("/tu/{proposal}")
@auth_required(True, redirect="/")
@account_type_required(REQUIRED_TYPES)
async def trusted_user_proposal_post(request: Request,
                                     proposal: int,
                                     decision: str = Form(...)):
    context = await make_variable_context(request, "Trusted User")
    proposal = int(proposal)  # Make sure it's an int.

    voteinfo = db.query(TUVoteInfo, TUVoteInfo.ID == proposal).first()
    if not voteinfo:
        raise HTTPException(status_code=int(HTTPStatus.NOT_FOUND))

    voters = db.query(User).join(TUVote).filter(TUVote.VoteID == voteinfo.ID)
    vote = db.query(TUVote, and_(TUVote.UserID == request.user.ID,
                                 TUVote.VoteID == voteinfo.ID)).first()

    status_code = HTTPStatus.OK
    if not request.user.is_trusted_user():
        context["error"] = "Only Trusted Users are allowed to vote."
        status_code = HTTPStatus.UNAUTHORIZED
    elif voteinfo.User == request.user.Username:
        context["error"] = "You cannot vote in an proposal about you."
        status_code = HTTPStatus.BAD_REQUEST
    elif vote is not None:
        context["error"] = "You've already voted for this proposal."
        status_code = HTTPStatus.BAD_REQUEST

    if status_code != HTTPStatus.OK:
        return render_proposal(request, context, proposal,
                               voteinfo, voters, vote,
                               status_code=status_code)

    if decision in {"Yes", "No", "Abstain"}:
        # Increment whichever decision was given to us.
        setattr(voteinfo, decision, getattr(voteinfo, decision) + 1)
    else:
        return Response("Invalid 'decision' value.",
                        status_code=int(HTTPStatus.BAD_REQUEST))

    with db.begin():
        vote = db.create(TUVote, User=request.user, VoteInfo=voteinfo)
        voteinfo.ActiveTUs += 1

    context["error"] = "You've already voted for this proposal."
    return render_proposal(request, context, proposal, voteinfo, voters, vote)


@router.get("/addvote")
@auth_required(True)
@account_type_required({"Trusted User", "Trusted User & Developer"})
async def trusted_user_addvote(request: Request,
                               user: str = str(),
                               type: str = "add_tu",
                               agenda: str = str()):
    context = await make_variable_context(request, "Add Proposal")

    if type not in ADDVOTE_SPECIFICS:
        context["error"] = "Invalid type."
        type = "add_tu"  # Default it.

    context["user"] = user
    context["type"] = type
    context["agenda"] = agenda

    return render_template(request, "addvote.html", context)


@router.post("/addvote")
@auth_required(True)
@account_type_required({TRUSTED_USER, TRUSTED_USER_AND_DEV})
async def trusted_user_addvote_post(request: Request,
                                    user: str = Form(default=str()),
                                    type: str = Form(default=str()),
                                    agenda: str = Form(default=str())):
    # Build a context.
    context = await make_variable_context(request, "Add Proposal")

    context["type"] = type
    context["user"] = user
    context["agenda"] = agenda

    def render_addvote(context, status_code):
        """ Simplify render_template a bit for this test. """
        return render_template(request, "addvote.html", context, status_code)

    # Alright, get some database records, if we can.
    if type != "bylaws":
        user_record = db.query(User, User.Username == user).first()
        if user_record is None:
            context["error"] = "Username does not exist."
            return render_addvote(context, HTTPStatus.NOT_FOUND)

        voteinfo = db.query(TUVoteInfo, TUVoteInfo.User == user).count()
        if voteinfo:
            _ = l10n.get_translator_for_request(request)
            context["error"] = _(
                "%s already has proposal running for them.") % (
                html.escape(user),)
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
    timestamp = int(datetime.utcnow().timestamp())

    # Remove <script> and <style> tags.
    agenda = re.sub(r'<[/]?script.*>', '', agenda)
    agenda = re.sub(r'<[/]?style.*>', '', agenda)

    # Create a new TUVoteInfo (proposal)!
    with db.begin():
        voteinfo = db.create(TUVoteInfo,
                             User=user,
                             Agenda=agenda,
                             Submitted=timestamp, End=timestamp + duration,
                             Quorum=quorum,
                             Submitter=request.user)

    # Redirect to the new proposal.
    return RedirectResponse(f"/tu/{voteinfo.ID}",
                            status_code=int(HTTPStatus.SEE_OTHER))
