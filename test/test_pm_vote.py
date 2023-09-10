import pytest
from sqlalchemy.exc import IntegrityError

from aurweb import db, time
from aurweb.models.account_type import PACKAGE_MAINTAINER_ID
from aurweb.models.user import User
from aurweb.models.vote import Vote
from aurweb.models.voteinfo import VoteInfo


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
def voteinfo(user: User) -> VoteInfo:
    ts = time.utcnow()
    with db.begin():
        voteinfo = db.create(
            VoteInfo,
            Agenda="Blah blah.",
            User=user.Username,
            Submitted=ts,
            End=ts + 5,
            Quorum=0.5,
            Submitter=user,
        )
    yield voteinfo


def test_vote_creation(user: User, voteinfo: VoteInfo):
    with db.begin():
        vote = db.create(Vote, User=user, VoteInfo=voteinfo)

    assert vote.VoteInfo == voteinfo
    assert vote.User == user
    assert vote in user.votes
    assert vote in voteinfo.votes


def test_vote_null_user_raises_exception(voteinfo: VoteInfo):
    with pytest.raises(IntegrityError):
        Vote(VoteInfo=voteinfo)


def test_vote_null_voteinfo_raises_exception(user: User):
    with pytest.raises(IntegrityError):
        Vote(User=user)
