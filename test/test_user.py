import hashlib

from datetime import datetime, timedelta

import bcrypt
import pytest

import aurweb.auth
import aurweb.config

from aurweb.db import query
from aurweb.models.account_type import AccountType
from aurweb.models.ban import Ban
from aurweb.models.session import Session
from aurweb.models.user import User
from aurweb.testing import setup_test_db
from aurweb.testing.models import make_session, make_user
from aurweb.testing.requests import Request

account_type, user = None, None


@pytest.fixture(autouse=True)
def setup():
    from aurweb.db import session

    global account_type, user

    setup_test_db("Users", "Sessions", "Bans")

    account_type = session.query(AccountType).filter(
        AccountType.AccountType == "User").first()

    user = make_user(Username="test", Email="test@example.org",
                     RealName="Test User", Passwd="testPassword",
                     AccountType=account_type)


def test_user_login_logout():
    """ Test creating a user and reading its columns. """
    from aurweb.db import session

    # Assert that make_user created a valid user.
    assert bool(user.ID)

    # Test authentication.
    assert user.valid_password("testPassword")
    assert not user.valid_password("badPassword")

    assert user in account_type.users

    # Make a raw request.
    request = Request()
    assert not user.login(request, "badPassword")
    assert not user.is_authenticated()

    sid = user.login(request, "testPassword")
    assert sid is not None
    assert user.is_authenticated()
    assert "AURSID" in request.cookies

    # Expect that User session relationships work right.
    user_session = session.query(Session).filter(
        Session.UsersID == user.ID).first()
    assert user_session == user.session
    assert user.session.SessionID == sid
    assert user.session.User == user

    # Search for the user via query API.
    result = session.query(User).filter(User.ID == user.ID).first()

    # Compare the result and our original user.
    assert result == user
    assert result.ID == user.ID
    assert result.AccountType.ID == user.AccountType.ID
    assert result.Username == user.Username
    assert result.Email == user.Email

    # Test result authenticate methods to ensure they work the same.
    assert not result.valid_password("badPassword")
    assert result.valid_password("testPassword")
    assert result.is_authenticated()

    # Ensure we've got the correct account type.
    assert user.AccountType.ID == account_type.ID
    assert user.AccountType.AccountType == account_type.AccountType

    # Test out user string functions.
    assert repr(user) == f"<User(ID='{user.ID}', " + \
        "AccountType='User', Username='test')>"

    # Test logout.
    user.logout(request)
    assert "AURSID" not in request.cookies
    assert not user.is_authenticated()


def test_user_login_twice():
    request = Request()
    assert user.login(request, "testPassword")
    assert user.login(request, "testPassword")


def test_user_login_banned():
    from aurweb.db import session

    # Add ban for the next 30 seconds.
    banned_timestamp = datetime.utcnow() + timedelta(seconds=30)
    ban = Ban(IPAddress="127.0.0.1", BanTS=banned_timestamp)
    session.add(ban)
    session.commit()

    request = Request()
    request.client.host = "127.0.0.1"
    assert not user.login(request, "testPassword")


def test_user_login_suspended():
    from aurweb.db import session
    user.Suspended = True
    session.commit()
    assert not user.login(Request(), "testPassword")


def test_legacy_user_authentication():
    from aurweb.db import session

    user.Salt = bcrypt.gensalt().decode()
    user.Passwd = hashlib.md5(f"{user.Salt}testPassword".encode()).hexdigest()
    session.commit()

    assert not user.valid_password("badPassword")
    assert user.valid_password("testPassword")

    # Test by passing a password of None value in.
    assert not user.valid_password(None)


def test_user_login_with_outdated_sid():
    from aurweb.db import session

    # Make a session with a LastUpdateTS 5 seconds ago, causing
    # user.login to update it with a new sid.
    _session = make_session(UsersID=user.ID, SessionID="stub",
                            LastUpdateTS=datetime.utcnow().timestamp() - 5)
    sid = user.login(Request(), "testPassword")
    assert sid and user.is_authenticated()
    assert sid != "stub"

    session.delete(_session)
    session.commit()


def test_user_update_password():
    user.update_password("secondPassword")
    assert not user.valid_password("testPassword")
    assert user.valid_password("secondPassword")


def test_user_minimum_passwd_length():
    passwd_min_len = aurweb.config.getint("options", "passwd_min_len")
    assert User.minimum_passwd_length() == passwd_min_len
