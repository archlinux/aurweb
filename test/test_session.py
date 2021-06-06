""" Test our Session model. """
from datetime import datetime
from unittest import mock

import pytest

from aurweb.db import create, query
from aurweb.models.account_type import AccountType
from aurweb.models.session import Session, generate_unique_sid
from aurweb.models.user import User
from aurweb.testing import setup_test_db

user = session = None


@pytest.fixture(autouse=True)
def setup():
    global user, session

    setup_test_db("Users", "Sessions")

    account_type = query(AccountType,
                         AccountType.AccountType == "User").first()
    user = create(User, Username="test", Email="test@example.org",
                  ResetKey="testReset", Passwd="testPassword",
                  AccountType=account_type)
    session = create(Session, UsersID=user.ID, SessionID="testSession",
                     LastUpdateTS=datetime.utcnow().timestamp())


def test_session():
    assert session.SessionID == "testSession"
    assert session.UsersID == user.ID


def test_session_cs():
    """ Test case sensitivity of the database table. """
    session_cs = create(Session, UsersID=user.ID,
                        SessionID="TESTSESSION",
                        LastUpdateTS=datetime.utcnow().timestamp())
    assert session_cs.SessionID == "TESTSESSION"
    assert session.SessionID == "testSession"


def test_session_user_association():
    # Make sure that the Session user attribute is correct.
    assert session.User == user


def test_generate_unique_sid():
    # Mock up aurweb.models.session.generate_sid by returning
    # sids[i % 2] from 0 .. n. This will swap between each sid
    # between each call.
    sids = ["testSession", "realSession"]
    i = 0

    def mock_generate_sid(length):
        nonlocal i
        sid = sids[i % 2]
        i += 1
        return sid

    with mock.patch("aurweb.util.make_random_string", mock_generate_sid):
        assert generate_unique_sid() == "realSession"
