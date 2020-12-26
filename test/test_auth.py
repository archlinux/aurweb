from datetime import datetime

import pytest

from starlette.authentication import AuthenticationError

from aurweb.db import query
from aurweb.auth import BasicAuthBackend
from aurweb.models.account_type import AccountType
from aurweb.testing import setup_test_db
from aurweb.testing.models import make_session, make_user
from aurweb.testing.requests import Request

# Persistent user object, initialized in our setup fixture.
user = None
backend = None
request = None


@pytest.fixture(autouse=True)
def setup():
    global user, backend, request

    setup_test_db("Users", "Sessions")

    from aurweb.db import session

    account_type = query(AccountType,
                         AccountType.AccountType == "User").first()
    user = make_user(Username="test", Email="test@example.com",
                     RealName="Test User", Passwd="testPassword",
                     AccountType=account_type)

    session.add(user)
    session.commit()

    backend = BasicAuthBackend()
    request = Request()


@pytest.mark.asyncio
async def test_auth_backend_missing_sid():
    # The request has no AURSID cookie, so authentication fails, and
    # AnonymousUser is returned.
    _, result = await backend.authenticate(request)
    assert not result.is_authenticated()


@pytest.mark.asyncio
async def test_auth_backend_invalid_sid():
    # Provide a fake AURSID that won't be found in the database.
    # This results in our path going down the invalid sid route,
    # which gives us an AnonymousUser.
    request.cookies["AURSID"] = "fake"
    _, result = await backend.authenticate(request)
    assert not result.is_authenticated()


@pytest.mark.asyncio
async def test_auth_backend_invalid_user_id():
    # Create a new session with a fake user id.
    now_ts = datetime.utcnow().timestamp()
    make_session(UsersID=666, SessionID="realSession",
                 LastUpdateTS=now_ts + 5)

    # Here, we specify a real SID; but it's user is not there.
    request.cookies["AURSID"] = "realSession"
    with pytest.raises(AuthenticationError, match="Invalid User ID: 666"):
        await backend.authenticate(request)


@pytest.mark.asyncio
async def test_basic_auth_backend():
    # This time, everything matches up. We expect the user to
    # equal the real_user.
    now_ts = datetime.utcnow().timestamp()
    make_session(UsersID=user.ID, SessionID="realSession",
                 LastUpdateTS=now_ts + 5)
    _, result = await backend.authenticate(request)
    assert result == user
