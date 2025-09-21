from typing import Generator

import fastapi
import pytest
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from aurweb import config, db, time
from aurweb.auth import (
    AnonymousUser,
    BasicAuthBackend,
    _auth_required,
    account_type_required,
)
from aurweb.models.account_type import USER, USER_ID
from aurweb.models.session import Session
from aurweb.models.user import User
from aurweb.testing.requests import Request


@pytest.fixture(autouse=True)
def setup(db_test):
    return


@pytest.fixture
def user() -> Generator[User]:
    with db.begin():
        user = db.create(
            User,
            Username="test",
            Email="test@example.com",
            RealName="Test User",
            Passwd="testPassword",
            AccountTypeID=USER_ID,
        )
    yield user


@pytest.fixture
def backend() -> Generator[BasicAuthBackend]:
    yield BasicAuthBackend()


@pytest.mark.asyncio
async def test_auth_backend_missing_sid(backend: BasicAuthBackend):
    # The request has no AURSID cookie, so authentication fails, and
    # AnonymousUser is returned.
    _, result = await backend.authenticate(Request())
    assert not result.is_authenticated()


@pytest.mark.asyncio
async def test_auth_backend_invalid_sid(backend: BasicAuthBackend):
    # Provide a fake AURSID that won't be found in the database.
    # This results in our path going down the invalid sid route,
    # which gives us an AnonymousUser.
    request = Request()
    request.cookies["AURSID"] = "fake"
    _, result = await backend.authenticate(request)
    assert not result.is_authenticated()


@pytest.mark.asyncio
async def test_auth_backend_invalid_user_id() -> None:
    # Create a new session with a fake user id.
    now_ts = time.utcnow()
    with pytest.raises(IntegrityError):
        Session(UsersID=666, SessionID="realSession", LastUpdateTS=now_ts + 5)


@pytest.mark.asyncio
async def test_basic_auth_backend(user: User, backend: BasicAuthBackend):
    # This time, everything matches up. We expect the user to
    # equal the real_user.
    now_ts = time.utcnow()
    with db.begin():
        db.create(
            Session, UsersID=user.ID, SessionID="realSession", LastUpdateTS=now_ts + 5
        )

    request = Request()
    request.cookies["AURSID"] = "realSession"
    _, result = await backend.authenticate(request)
    assert result == user


@pytest.mark.asyncio
async def test_expired_session(backend: BasicAuthBackend, user: User):
    """Login, expire the session manually, then authenticate."""
    # First, build a Request with a logged  in user.
    request = Request()
    request.user = user
    sid = request.user.login(Request(), "testPassword")
    request.cookies["AURSID"] = sid

    # Set Session.LastUpdateTS to 20 seconds expired.
    timeout = config.getint("options", "login_timeout")
    now_ts = time.utcnow()
    with db.begin():
        request.user.session.LastUpdateTS = now_ts - timeout - 20

    # Run through authentication backend and get the session
    # deleted due to its expiration.
    await backend.authenticate(request)
    session = db.query(Session).filter(Session.SessionID == sid).first()
    assert session is None


@pytest.mark.asyncio
async def test_auth_required_redirection_bad_referrer() -> None:
    # Create a fake route function which can be wrapped by auth_required.
    def bad_referrer_route(request: fastapi.Request):
        pass

    # Get down to the nitty gritty internal wrapper.
    bad_referrer_route = _auth_required()(bad_referrer_route)

    # Execute the route with a "./blahblahblah" Referer, which does not
    # match aur_location; `./` has been used as a prefix to attempt to
    # ensure we're providing a fake referer.
    with pytest.raises(HTTPException) as exc:
        request = Request(method="POST", headers={"Referer": "./blahblahblah"})
        await bad_referrer_route(request)
        assert exc.detail == "Bad Referer header."


def test_account_type_required() -> None:
    """This test merely asserts that a few different paths
    do not raise exceptions."""
    # This one shouldn't raise.
    account_type_required({USER})

    # This one also shouldn't raise.
    account_type_required({USER_ID})

    # But this one should! We have no "FAKE" key.
    with pytest.raises(KeyError):
        account_type_required({"FAKE"})


def test_is_package_maintainer() -> None:
    user_ = AnonymousUser()
    assert not user_.is_package_maintainer()


def test_is_developer() -> None:
    user_ = AnonymousUser()
    assert not user_.is_developer()


def test_is_elevated() -> None:
    user_ = AnonymousUser()
    assert not user_.is_elevated()


def test_voted_for() -> None:
    user_ = AnonymousUser()
    assert not user_.voted_for(None)


def test_notified() -> None:
    user_ = AnonymousUser()
    assert not user_.notified(None)
