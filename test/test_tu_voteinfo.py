from datetime import datetime

import pytest

from sqlalchemy.exc import IntegrityError

from aurweb import db
from aurweb.db import create, rollback
from aurweb.models.account_type import TRUSTED_USER_ID
from aurweb.models.tu_voteinfo import TUVoteInfo
from aurweb.models.user import User


@pytest.fixture(autouse=True)
def setup(db_test):
    return


@pytest.fixture
def user() -> User:
    with db.begin():
        user = create(User, Username="test", Email="test@example.org",
                      RealName="Test User", Passwd="testPassword",
                      AccountTypeID=TRUSTED_USER_ID)
    yield user


def test_tu_voteinfo_creation(user: User):
    ts = int(datetime.utcnow().timestamp())
    with db.begin():
        tu_voteinfo = create(TUVoteInfo,
                             Agenda="Blah blah.",
                             User=user.Username,
                             Submitted=ts, End=ts + 5,
                             Quorum=0.5,
                             Submitter=user)
    assert bool(tu_voteinfo.ID)
    assert tu_voteinfo.Agenda == "Blah blah."
    assert tu_voteinfo.User == user.Username
    assert tu_voteinfo.Submitted == ts
    assert tu_voteinfo.End == ts + 5
    assert tu_voteinfo.Quorum == 0.5
    assert tu_voteinfo.Submitter == user
    assert tu_voteinfo.Yes == 0
    assert tu_voteinfo.No == 0
    assert tu_voteinfo.Abstain == 0
    assert tu_voteinfo.ActiveTUs == 0

    assert tu_voteinfo in user.tu_voteinfo_set


def test_tu_voteinfo_is_running(user: User):
    ts = int(datetime.utcnow().timestamp())
    with db.begin():
        tu_voteinfo = create(TUVoteInfo,
                             Agenda="Blah blah.",
                             User=user.Username,
                             Submitted=ts, End=ts + 1000,
                             Quorum=0.5,
                             Submitter=user)
    assert tu_voteinfo.is_running() is True

    with db.begin():
        tu_voteinfo.End = ts - 5
    assert tu_voteinfo.is_running() is False


def test_tu_voteinfo_total_votes(user: User):
    ts = int(datetime.utcnow().timestamp())
    with db.begin():
        tu_voteinfo = create(TUVoteInfo,
                             Agenda="Blah blah.",
                             User=user.Username,
                             Submitted=ts, End=ts + 1000,
                             Quorum=0.5,
                             Submitter=user)

        tu_voteinfo.Yes = 1
        tu_voteinfo.No = 3
        tu_voteinfo.Abstain = 5

    # total_votes() should be the sum of Yes, No and Abstain: 1 + 3 + 5 = 9.
    assert tu_voteinfo.total_votes() == 9


def test_tu_voteinfo_null_submitter_raises(user: User):
    with pytest.raises(IntegrityError):
        with db.begin():
            create(TUVoteInfo,
                   Agenda="Blah blah.",
                   User=user.Username,
                   Submitted=0, End=0,
                   Quorum=0.50)
    rollback()


def test_tu_voteinfo_null_agenda_raises(user: User):
    with pytest.raises(IntegrityError):
        with db.begin():
            create(TUVoteInfo,
                   User=user.Username,
                   Submitted=0, End=0,
                   Quorum=0.50,
                   Submitter=user)
    rollback()


def test_tu_voteinfo_null_user_raises(user: User):
    with pytest.raises(IntegrityError):
        with db.begin():
            create(TUVoteInfo,
                   Agenda="Blah blah.",
                   Submitted=0, End=0,
                   Quorum=0.50,
                   Submitter=user)
    rollback()


def test_tu_voteinfo_null_submitted_raises(user: User):
    with pytest.raises(IntegrityError):
        with db.begin():
            create(TUVoteInfo,
                   Agenda="Blah blah.",
                   User=user.Username,
                   End=0,
                   Quorum=0.50,
                   Submitter=user)
    rollback()


def test_tu_voteinfo_null_end_raises(user: User):
    with pytest.raises(IntegrityError):
        with db.begin():
            create(TUVoteInfo,
                   Agenda="Blah blah.",
                   User=user.Username,
                   Submitted=0,
                   Quorum=0.50,
                   Submitter=user)
    rollback()


def test_tu_voteinfo_null_quorum_raises(user: User):
    with pytest.raises(IntegrityError):
        with db.begin():
            create(TUVoteInfo,
                   Agenda="Blah blah.",
                   User=user.Username,
                   Submitted=0, End=0,
                   Submitter=user)
    rollback()
