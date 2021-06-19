import typing

from datetime import datetime
from http import HTTPStatus
from urllib.parse import quote_plus

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import Response
from sqlalchemy import and_, or_

from aurweb import db
from aurweb.auth import account_type_required, auth_required
from aurweb.models.account_type import DEVELOPER, TRUSTED_USER, TRUSTED_USER_AND_DEV
from aurweb.models.tu_vote import TUVote
from aurweb.models.tu_voteinfo import TUVoteInfo
from aurweb.models.user import User
from aurweb.templates import make_context, make_variable_context, render_template

router = APIRouter()

# Some TU route specific constants.
ITEMS_PER_PAGE = 10  # Paged table size.
MAX_AGENDA_LENGTH = 75  # Agenda table column length.

# A set of account types that will approve a user for TU actions.
REQUIRED_TYPES = {
    TRUSTED_USER,
    DEVELOPER,
    TRUSTED_USER_AND_DEV
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

    context["q"] = '&'.join([
        f"coff={current_off}",
        f"cby={quote_plus(current_by)}",
        f"poff={past_off}",
        f"pby={quote_plus(past_by)}"
    ])

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
    context["voters"] = voters

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

    # status_code we'll use for responses later.
    status_code = HTTPStatus.OK

    if not request.user.is_trusted_user():
        # Test: Create a proposal and view it as a "Developer". It
        # should give us this error.
        context["error"] = "Only Trusted Users are allowed to vote."
        status_code = HTTPStatus.UNAUTHORIZED
    elif voteinfo.User == request.user.Username:
        context["error"] = "You cannot vote in an proposal about you."
        status_code = HTTPStatus.BAD_REQUEST

    vote = db.query(TUVote, and_(TUVote.UserID == request.user.ID,
                                 TUVote.VoteID == voteinfo.ID)).first()

    if status_code != HTTPStatus.OK:
        return render_proposal(request, context, proposal,
                               voteinfo, voters, vote,
                               status_code=status_code)

    if vote is not None:
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

    vote = db.create(TUVote, User=request.user, VoteInfo=voteinfo,
                     autocommit=False)
    voteinfo.ActiveTUs += 1
    db.commit()

    context["error"] = "You've already voted for this proposal."
    return render_proposal(request, context, proposal, voteinfo, voters, vote)
