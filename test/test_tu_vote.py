import pytest

from sqlalchemy.exc import IntegrityError

from aurweb import db, time
from aurweb.models.account_type import TRUSTED_USER_ID
from aurweb.models.tu_vote import TUVote
from aurweb.models.tu_voteinfo import TUVoteInfo
from aurweb.models.user import User


@pytest.fixture(autouse=True)
def setup(db_test):
    return


@pytest.fixture
def user() -> User:
    with db.begin():
        user = db.create(User, Username="test", Email="test@example.org",
                         RealName="Test User", Passwd="testPassword",
                         AccountTypeID=TRUSTED_USER_ID)
    yield user


@pytest.fixture
def tu_voteinfo(user: User) -> TUVoteInfo:
    ts = time.utcnow()
    with db.begin():
        tu_voteinfo = db.create(TUVoteInfo, Agenda="Blah blah.",
                                User=user.Username,
                                Submitted=ts, End=ts + 5,
                                Quorum=0.5, Submitter=user)
    yield tu_voteinfo


def test_tu_vote_creation(user: User, tu_voteinfo: TUVoteInfo):
    with db.begin():
        tu_vote = db.create(TUVote, User=user, VoteInfo=tu_voteinfo)

    assert tu_vote.VoteInfo == tu_voteinfo
    assert tu_vote.User == user
    assert tu_vote in user.tu_votes
    assert tu_vote in tu_voteinfo.tu_votes


def test_tu_vote_null_user_raises_exception(tu_voteinfo: TUVoteInfo):
    with pytest.raises(IntegrityError):
        TUVote(VoteInfo=tu_voteinfo)


def test_tu_vote_null_voteinfo_raises_exception(user: User):
    with pytest.raises(IntegrityError):
        TUVote(User=user)
