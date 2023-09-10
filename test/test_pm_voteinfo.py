import pytest
from sqlalchemy.exc import IntegrityError

from aurweb import db, time
from aurweb.db import create, rollback
from aurweb.models.account_type import PACKAGE_MAINTAINER_ID
from aurweb.models.tu_voteinfo import TUVoteInfo
from aurweb.models.user import User


@pytest.fixture(autouse=True)
def setup(db_test):
    return


@pytest.fixture
def user() -> User:
    with db.begin():
        user = create(
            User,
            Username="test",
            Email="test@example.org",
            RealName="Test User",
            Passwd="testPassword",
            AccountTypeID=PACKAGE_MAINTAINER_ID,
        )
    yield user


def test_pm_voteinfo_creation(user: User):
    ts = time.utcnow()
    with db.begin():
        pm_voteinfo = create(
            TUVoteInfo,
            Agenda="Blah blah.",
            User=user.Username,
            Submitted=ts,
            End=ts + 5,
            Quorum=0.5,
            Submitter=user,
        )
    assert bool(pm_voteinfo.ID)
    assert pm_voteinfo.Agenda == "Blah blah."
    assert pm_voteinfo.User == user.Username
    assert pm_voteinfo.Submitted == ts
    assert pm_voteinfo.End == ts + 5
    assert pm_voteinfo.Quorum == 0.5
    assert pm_voteinfo.Submitter == user
    assert pm_voteinfo.Yes == 0
    assert pm_voteinfo.No == 0
    assert pm_voteinfo.Abstain == 0
    assert pm_voteinfo.ActiveTUs == 0

    assert pm_voteinfo in user.tu_voteinfo_set


def test_pm_voteinfo_is_running(user: User):
    ts = time.utcnow()
    with db.begin():
        pm_voteinfo = create(
            TUVoteInfo,
            Agenda="Blah blah.",
            User=user.Username,
            Submitted=ts,
            End=ts + 1000,
            Quorum=0.5,
            Submitter=user,
        )
    assert pm_voteinfo.is_running() is True

    with db.begin():
        pm_voteinfo.End = ts - 5
    assert pm_voteinfo.is_running() is False


def test_pm_voteinfo_total_votes(user: User):
    ts = time.utcnow()
    with db.begin():
        pm_voteinfo = create(
            TUVoteInfo,
            Agenda="Blah blah.",
            User=user.Username,
            Submitted=ts,
            End=ts + 1000,
            Quorum=0.5,
            Submitter=user,
        )

        pm_voteinfo.Yes = 1
        pm_voteinfo.No = 3
        pm_voteinfo.Abstain = 5

    # total_votes() should be the sum of Yes, No and Abstain: 1 + 3 + 5 = 9.
    assert pm_voteinfo.total_votes() == 9


def test_pm_voteinfo_null_submitter_raises(user: User):
    with pytest.raises(IntegrityError):
        with db.begin():
            create(
                TUVoteInfo,
                Agenda="Blah blah.",
                User=user.Username,
                Submitted=0,
                End=0,
                Quorum=0.50,
            )
    rollback()


def test_pm_voteinfo_null_agenda_raises(user: User):
    with pytest.raises(IntegrityError):
        with db.begin():
            create(
                TUVoteInfo,
                User=user.Username,
                Submitted=0,
                End=0,
                Quorum=0.50,
                Submitter=user,
            )
    rollback()


def test_pm_voteinfo_null_user_raises(user: User):
    with pytest.raises(IntegrityError):
        with db.begin():
            create(
                TUVoteInfo,
                Agenda="Blah blah.",
                Submitted=0,
                End=0,
                Quorum=0.50,
                Submitter=user,
            )
    rollback()


def test_pm_voteinfo_null_submitted_raises(user: User):
    with pytest.raises(IntegrityError):
        with db.begin():
            create(
                TUVoteInfo,
                Agenda="Blah blah.",
                User=user.Username,
                End=0,
                Quorum=0.50,
                Submitter=user,
            )
    rollback()


def test_pm_voteinfo_null_end_raises(user: User):
    with pytest.raises(IntegrityError):
        with db.begin():
            create(
                TUVoteInfo,
                Agenda="Blah blah.",
                User=user.Username,
                Submitted=0,
                Quorum=0.50,
                Submitter=user,
            )
    rollback()


def test_pm_voteinfo_null_quorum_default(user: User):
    with db.begin():
        vi = create(
            TUVoteInfo,
            Agenda="Blah blah.",
            User=user.Username,
            Submitted=0,
            End=0,
            Submitter=user,
        )
    assert vi.Quorum == 0
