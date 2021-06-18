from datetime import datetime

import pytest

from sqlalchemy.exc import IntegrityError

from aurweb.db import commit, create, query, rollback
from aurweb.models.account_type import AccountType
from aurweb.models.tu_voteinfo import TUVoteInfo
from aurweb.models.user import User
from aurweb.testing import setup_test_db

user = None


@pytest.fixture(autouse=True)
def setup():
    global user

    setup_test_db("Users", "PackageBases", "TU_VoteInfo")

    tu_type = query(AccountType,
                    AccountType.AccountType == "Trusted User").first()
    user = create(User, Username="test", Email="test@example.org",
                  RealName="Test User", Passwd="testPassword",
                  AccountType=tu_type)


def test_tu_voteinfo_creation():
    ts = int(datetime.utcnow().timestamp())
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


def test_tu_voteinfo_is_running():
    ts = int(datetime.utcnow().timestamp())
    tu_voteinfo = create(TUVoteInfo,
                         Agenda="Blah blah.",
                         User=user.Username,
                         Submitted=ts, End=ts + 1000,
                         Quorum=0.5,
                         Submitter=user)
    assert tu_voteinfo.is_running() is True

    tu_voteinfo.End = ts - 5
    commit()
    assert tu_voteinfo.is_running() is False


def test_tu_voteinfo_null_submitter_raises_exception():
    with pytest.raises(IntegrityError):
        create(TUVoteInfo,
               Agenda="Blah blah.",
               User=user.Username,
               Submitted=0, End=0,
               Quorum=0.50)
    rollback()


def test_tu_voteinfo_null_agenda_raises_exception():
    with pytest.raises(IntegrityError):
        create(TUVoteInfo,
               User=user.Username,
               Submitted=0, End=0,
               Quorum=0.50,
               Submitter=user)
    rollback()


def test_tu_voteinfo_null_user_raises_exception():
    with pytest.raises(IntegrityError):
        create(TUVoteInfo,
               Agenda="Blah blah.",
               Submitted=0, End=0,
               Quorum=0.50,
               Submitter=user)
    rollback()


def test_tu_voteinfo_null_submitted_raises_exception():
    with pytest.raises(IntegrityError):
        create(TUVoteInfo,
               Agenda="Blah blah.",
               User=user.Username,
               End=0,
               Quorum=0.50,
               Submitter=user)
    rollback()


def test_tu_voteinfo_null_end_raises_exception():
    with pytest.raises(IntegrityError):
        create(TUVoteInfo,
               Agenda="Blah blah.",
               User=user.Username,
               Submitted=0,
               Quorum=0.50,
               Submitter=user)
    rollback()


def test_tu_voteinfo_null_quorum_raises_exception():
    with pytest.raises(IntegrityError):
        create(TUVoteInfo,
               Agenda="Blah blah.",
               User=user.Username,
               Submitted=0, End=0,
               Submitter=user)
    rollback()
