""" Test our Session model. """
from unittest import mock

import pytest

from sqlalchemy.exc import IntegrityError

from aurweb import db, time
from aurweb.models.account_type import USER_ID
from aurweb.models.session import Session, generate_unique_sid
from aurweb.models.user import User


@pytest.fixture(autouse=True)
def setup(db_test):
    return


@pytest.fixture
def user() -> User:
    with db.begin():
        user = db.create(User, Username="test", Email="test@example.org",
                         ResetKey="testReset", Passwd="testPassword",
                         AccountTypeID=USER_ID)
    yield user


@pytest.fixture
def session(user: User) -> Session:
    with db.begin():
        session = db.create(Session, User=user, SessionID="testSession",
                            LastUpdateTS=time.utcnow())
    yield session


def test_session(user: User, session: Session):
    assert session.SessionID == "testSession"
    assert session.UsersID == user.ID


def test_session_cs():
    """ Test case sensitivity of the database table. """
    with db.begin():
        user2 = db.create(User, Username="test2", Email="test2@example.org",
                          ResetKey="testReset2", Passwd="testPassword",
                          AccountTypeID=USER_ID)

    with db.begin():
        session_cs = db.create(Session, User=user2, SessionID="TESTSESSION",
                               LastUpdateTS=time.utcnow())

    assert session_cs.SessionID == "TESTSESSION"
    assert session_cs.SessionID != "testSession"


def test_session_user_association(user: User, session: Session):
    # Make sure that the Session user attribute is correct.
    assert session.User == user


def test_session_null_user_raises():
    with pytest.raises(IntegrityError):
        Session()


def test_generate_unique_sid(session: Session):
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
