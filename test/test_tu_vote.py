from datetime import datetime

import pytest

from sqlalchemy.exc import IntegrityError

from aurweb import db
from aurweb.models.account_type import TRUSTED_USER_ID
from aurweb.models.tu_vote import TUVote
from aurweb.models.tu_voteinfo import TUVoteInfo
from aurweb.models.user import User

user = tu_voteinfo = None


@pytest.fixture(autouse=True)
def setup(db_test):
    global user, tu_voteinfo

    ts = int(datetime.utcnow().timestamp())
    with db.begin():
        user = db.create(User, Username="test", Email="test@example.org",
                         RealName="Test User", Passwd="testPassword",
                         AccountTypeID=TRUSTED_USER_ID)

        tu_voteinfo = db.create(TUVoteInfo,
                                Agenda="Blah blah.",
                                User=user.Username,
                                Submitted=ts, End=ts + 5,
                                Quorum=0.5,
                                Submitter=user)


def test_tu_vote_creation():
    with db.begin():
        tu_vote = db.create(TUVote, User=user, VoteInfo=tu_voteinfo)

    assert tu_vote.VoteInfo == tu_voteinfo
    assert tu_vote.User == user
    assert tu_vote in user.tu_votes
    assert tu_vote in tu_voteinfo.tu_votes


def test_tu_vote_null_user_raises_exception():
    with pytest.raises(IntegrityError):
        TUVote(VoteInfo=tu_voteinfo)


def test_tu_vote_null_voteinfo_raises_exception():
    with pytest.raises(IntegrityError):
        TUVote(User=user)
