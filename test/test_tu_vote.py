from datetime import datetime

import pytest

from sqlalchemy.exc import IntegrityError

from aurweb.db import create, query, rollback
from aurweb.models.account_type import AccountType
from aurweb.models.tu_vote import TUVote
from aurweb.models.tu_voteinfo import TUVoteInfo
from aurweb.models.user import User
from aurweb.testing import setup_test_db

user = tu_voteinfo = None


@pytest.fixture(autouse=True)
def setup():
    global user, tu_voteinfo

    setup_test_db("Users", "TU_VoteInfo", "TU_Votes")

    tu_type = query(AccountType,
                    AccountType.AccountType == "Trusted User").first()
    user = create(User, Username="test", Email="test@example.org",
                  RealName="Test User", Passwd="testPassword",
                  AccountType=tu_type)

    ts = int(datetime.utcnow().timestamp())
    tu_voteinfo = create(TUVoteInfo,
                         Agenda="Blah blah.",
                         User=user.Username,
                         Submitted=ts, End=ts + 5,
                         Quorum=0.5,
                         Submitter=user)


def test_tu_vote_creation():
    tu_vote = create(TUVote, User=user, VoteInfo=tu_voteinfo)
    assert tu_vote.VoteInfo == tu_voteinfo
    assert tu_vote.User == user

    assert tu_vote in user.tu_votes
    assert tu_vote in tu_voteinfo.tu_votes


def test_tu_vote_null_user_raises_exception():
    with pytest.raises(IntegrityError):
        create(TUVote, VoteInfo=tu_voteinfo)
    rollback()


def test_tu_vote_null_voteinfo_raises_exception():
    with pytest.raises(IntegrityError):
        create(TUVote, User=user)
    rollback()
