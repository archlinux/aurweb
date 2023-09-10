import pytest
from sqlalchemy.exc import IntegrityError

from aurweb import db, time
from aurweb.models.account_type import PACKAGE_MAINTAINER_ID
from aurweb.models.tu_vote import TUVote
from aurweb.models.tu_voteinfo import TUVoteInfo
from aurweb.models.user import User


@pytest.fixture(autouse=True)
def setup(db_test):
    return


@pytest.fixture
def user() -> User:
    with db.begin():
        user = db.create(
            User,
            Username="test",
            Email="test@example.org",
            RealName="Test User",
            Passwd="testPassword",
            AccountTypeID=PACKAGE_MAINTAINER_ID,
        )
    yield user


@pytest.fixture
def pm_voteinfo(user: User) -> TUVoteInfo:
    ts = time.utcnow()
    with db.begin():
        pm_voteinfo = db.create(
            TUVoteInfo,
            Agenda="Blah blah.",
            User=user.Username,
            Submitted=ts,
            End=ts + 5,
            Quorum=0.5,
            Submitter=user,
        )
    yield pm_voteinfo


def test_pm_vote_creation(user: User, pm_voteinfo: TUVoteInfo):
    with db.begin():
        pm_vote = db.create(TUVote, User=user, VoteInfo=pm_voteinfo)

    assert pm_vote.VoteInfo == pm_voteinfo
    assert pm_vote.User == user
    assert pm_vote in user.tu_votes
    assert pm_vote in pm_voteinfo.tu_votes


def test_pm_vote_null_user_raises_exception(pm_voteinfo: TUVoteInfo):
    with pytest.raises(IntegrityError):
        TUVote(VoteInfo=pm_voteinfo)


def test_pm_vote_null_voteinfo_raises_exception(user: User):
    with pytest.raises(IntegrityError):
        TUVote(User=user)
