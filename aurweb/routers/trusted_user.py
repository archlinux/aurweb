from datetime import datetime
from urllib.parse import quote_plus

from fastapi import APIRouter, Request
from sqlalchemy import and_, or_

from aurweb import db
from aurweb.auth import account_type_required, auth_required
from aurweb.models.account_type import DEVELOPER, TRUSTED_USER, TRUSTED_USER_AND_DEV
from aurweb.models.tu_vote import TUVote
from aurweb.models.tu_voteinfo import TUVoteInfo
from aurweb.models.user import User
from aurweb.templates import make_context, render_template

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
