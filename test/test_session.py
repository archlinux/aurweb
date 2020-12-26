""" Test our Session model. """
from datetime import datetime
from unittest import mock

import pytest

from aurweb.models.account_type import AccountType
from aurweb.models.session import generate_unique_sid
from aurweb.testing import setup_test_db
from aurweb.testing.models import make_session, make_user

user, _session = None, None


@pytest.fixture(autouse=True)
def setup():
    from aurweb.db import session

    global user, _session

    setup_test_db("Users", "Sessions")

    account_type = session.query(AccountType).filter(
        AccountType.AccountType == "User").first()
    user = make_user(Username="test", Email="test@example.org",
                     ResetKey="testReset", Passwd="testPassword",
                     AccountType=account_type)
    _session = make_session(UsersID=user.ID, SessionID="testSession",
                            LastUpdateTS=datetime.utcnow())


def test_session():
    assert _session.SessionID == "testSession"
    assert _session.UsersID == user.ID


def test_session_user_association():
    # Make sure that the Session user attribute is correct.
    assert _session.User == user


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
