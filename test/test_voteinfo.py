from typing import Generator

import pytest
from sqlalchemy.exc import IntegrityError

from aurweb import db, time
from aurweb.db import create, rollback
from aurweb.models.account_type import PACKAGE_MAINTAINER_ID
from aurweb.models.user import User
from aurweb.models.voteinfo import VoteInfo


@pytest.fixture(autouse=True)
def setup(db_test):
    return


@pytest.fixture
def user() -> Generator[User]:
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


def test_voteinfo_creation(user: User):
    ts = time.utcnow()
    with db.begin():
        voteinfo = create(
            VoteInfo,
            Agenda="Blah blah.",
            User=user.Username,
            Submitted=ts,
            End=ts + 5,
            Quorum=0.5,
            Submitter=user,
        )
    assert bool(voteinfo.ID)
    assert voteinfo.Agenda == "Blah blah."
    assert voteinfo.User == user.Username
    assert voteinfo.Submitted == ts
    assert voteinfo.End == ts + 5
    assert voteinfo.Quorum == 0.5
    assert voteinfo.Submitter == user
    assert voteinfo.Yes == 0
    assert voteinfo.No == 0
    assert voteinfo.Abstain == 0
    assert voteinfo.ActiveUsers == 0

    assert voteinfo in user.voteinfo_set


def test_voteinfo_is_running(user: User):
    ts = time.utcnow()
    with db.begin():
        voteinfo = create(
            VoteInfo,
            Agenda="Blah blah.",
            User=user.Username,
            Submitted=ts,
            End=ts + 1000,
            Quorum=0.5,
            Submitter=user,
        )
    assert voteinfo.is_running() is True

    with db.begin():
        voteinfo.End = ts - 5
    assert voteinfo.is_running() is False


def test_voteinfo_total_votes(user: User):
    ts = time.utcnow()
    with db.begin():
        voteinfo = create(
            VoteInfo,
            Agenda="Blah blah.",
            User=user.Username,
            Submitted=ts,
            End=ts + 1000,
            Quorum=0.5,
            Submitter=user,
        )

        voteinfo.Yes = 1
        voteinfo.No = 3
        voteinfo.Abstain = 5

    # total_votes() should be the sum of Yes, No and Abstain: 1 + 3 + 5 = 9.
    assert voteinfo.total_votes() == 9


def test_voteinfo_null_submitter_raises(user: User):
    with pytest.raises(IntegrityError):
        with db.begin():
            create(
                VoteInfo,
                Agenda="Blah blah.",
                User=user.Username,
                Submitted=0,
                End=0,
                Quorum=0.50,
            )
    rollback()


def test_voteinfo_null_agenda_raises(user: User):
    with pytest.raises(IntegrityError):
        with db.begin():
            create(
                VoteInfo,
                User=user.Username,
                Submitted=0,
                End=0,
                Quorum=0.50,
                Submitter=user,
            )
    rollback()


def test_voteinfo_null_user_raises(user: User):
    with pytest.raises(IntegrityError):
        with db.begin():
            create(
                VoteInfo,
                Agenda="Blah blah.",
                Submitted=0,
                End=0,
                Quorum=0.50,
                Submitter=user,
            )
    rollback()


def test_voteinfo_null_submitted_raises(user: User):
    with pytest.raises(IntegrityError):
        with db.begin():
            create(
                VoteInfo,
                Agenda="Blah blah.",
                User=user.Username,
                End=0,
                Quorum=0.50,
                Submitter=user,
            )
    rollback()


def test_voteinfo_null_end_raises(user: User):
    with pytest.raises(IntegrityError):
        with db.begin():
            create(
                VoteInfo,
                Agenda="Blah blah.",
                User=user.Username,
                Submitted=0,
                Quorum=0.50,
                Submitter=user,
            )
    rollback()


def test_voteinfo_null_quorum_default(user: User):
    with db.begin():
        vi = create(
            VoteInfo,
            Agenda="Blah blah.",
            User=user.Username,
            Submitted=0,
            End=0,
            Submitter=user,
        )
    assert vi.Quorum == 0
