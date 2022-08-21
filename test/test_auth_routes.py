import re
from http import HTTPStatus
from unittest import mock

import pytest
from fastapi.testclient import TestClient

import aurweb.config
from aurweb import db, time
from aurweb.asgi import app
from aurweb.models.account_type import USER_ID
from aurweb.models.session import Session
from aurweb.models.user import User
from aurweb.testing.html import get_errors

# Some test global constants.
TEST_USERNAME = "test"
TEST_EMAIL = "test@example.org"
TEST_REFERER = {
    "referer": aurweb.config.get("options", "aur_location") + "/login",
}


@pytest.fixture(autouse=True)
def setup(db_test):
    return


@pytest.fixture
def client() -> TestClient:
    client = TestClient(app=app)

    # Necessary for forged login CSRF protection on the login route. Set here
    # instead of only on the necessary requests for convenience.
    client.headers.update(TEST_REFERER)
    yield client


@pytest.fixture
def user() -> User:
    with db.begin():
        user = db.create(
            User,
            Username=TEST_USERNAME,
            Email=TEST_EMAIL,
            RealName="Test User",
            Passwd="testPassword",
            AccountTypeID=USER_ID,
        )
    yield user


def test_login_logout(client: TestClient, user: User):
    post_data = {"user": "test", "passwd": "testPassword", "next": "/"}

    with client as request:
        # First, let's test get /login.
        response = request.get("/login")
        assert response.status_code == int(HTTPStatus.OK)

        response = request.post("/login", data=post_data, allow_redirects=False)
        assert response.status_code == int(HTTPStatus.SEE_OTHER)

        # Simulate following the redirect location from above's response.
        response = request.get(response.headers.get("location"))
        assert response.status_code == int(HTTPStatus.OK)

        response = request.post("/logout", data=post_data, allow_redirects=False)
        assert response.status_code == int(HTTPStatus.SEE_OTHER)

        response = request.post(
            "/logout",
            data=post_data,
            cookies={"AURSID": response.cookies.get("AURSID")},
            allow_redirects=False,
        )
        assert response.status_code == int(HTTPStatus.SEE_OTHER)

    assert "AURSID" not in response.cookies


def test_login_suspended(client: TestClient, user: User):
    with db.begin():
        user.Suspended = 1

    data = {"user": user.Username, "passwd": "testPassword", "next": "/"}
    with client as request:
        resp = request.post("/login", data=data)
    errors = get_errors(resp.text)
    assert errors[0].text.strip() == "Account Suspended"


def test_login_email(client: TestClient, user: user):
    post_data = {"user": user.Email, "passwd": "testPassword", "next": "/"}

    with client as request:
        resp = request.post("/login", data=post_data, allow_redirects=False)
    assert resp.status_code == int(HTTPStatus.SEE_OTHER)
    assert "AURSID" in resp.cookies


def mock_getboolean(**overrided_configs):
    mocked_config = {
        tuple(config.split("__")): value for config, value in overrided_configs.items()
    }

    def side_effect(*args):
        return mocked_config.get(args, bool(aurweb.config.get(*args)))

    return side_effect


@mock.patch(
    "aurweb.config.getboolean",
    side_effect=mock_getboolean(options__disable_http_login=False),
)
def test_insecure_login(getboolean: mock.Mock, client: TestClient, user: User):
    post_data = {"user": user.Username, "passwd": "testPassword", "next": "/"}

    # Perform a login request with the data matching our user.
    with client as request:
        response = request.post("/login", data=post_data, allow_redirects=False)

    # Make sure we got the expected status out of it.
    assert response.status_code == int(HTTPStatus.SEE_OTHER)

    # Let's check what we got in terms of cookies for AURSID.
    # Make sure that a secure cookie got passed to us.
    cookie = next(c for c in response.cookies if c.name == "AURSID")
    assert cookie.secure is False
    assert cookie.has_nonstandard_attr("HttpOnly") is False
    assert cookie.has_nonstandard_attr("SameSite") is True
    assert cookie.get_nonstandard_attr("SameSite") == "lax"
    assert cookie.value is not None and len(cookie.value) > 0


@mock.patch(
    "aurweb.config.getboolean",
    side_effect=mock_getboolean(options__disable_http_login=True),
)
def test_secure_login(getboolean: mock.Mock, client: TestClient, user: User):
    """In this test, we check to verify the course of action taken
    by starlette when providing secure=True to a response cookie.
    This is achieved by mocking aurweb.config.getboolean to return
    True (or 1) when looking for `options.disable_http_login`.
    When we receive a response with `disable_http_login` enabled,
    we check the fields in cookies received for the secure and
    httponly fields, in addition to the rest of the fields given
    on such a request."""

    # Create a local TestClient here since we mocked configuration.
    # client = TestClient(app)

    # Necessary for forged login CSRF protection on the login route. Set here
    # instead of only on the necessary requests for convenience.
    # client.headers.update(TEST_REFERER)

    # Data used for our upcoming http post request.
    post_data = {"user": user.Username, "passwd": "testPassword", "next": "/"}

    # Perform a login request with the data matching our user.
    with client as request:
        response = request.post("/login", data=post_data, allow_redirects=False)

    # Make sure we got the expected status out of it.
    assert response.status_code == int(HTTPStatus.SEE_OTHER)

    # Let's check what we got in terms of cookies for AURSID.
    # Make sure that a secure cookie got passed to us.
    cookie = next(c for c in response.cookies if c.name == "AURSID")
    assert cookie.secure is True
    assert cookie.has_nonstandard_attr("HttpOnly") is True
    assert cookie.has_nonstandard_attr("SameSite") is True
    assert cookie.get_nonstandard_attr("SameSite") == "lax"
    assert cookie.value is not None and len(cookie.value) > 0

    # Let's make sure we actually have a session relationship
    # with the AURSID we ended up with.
    record = db.query(Session, Session.SessionID == cookie.value).first()
    assert record is not None and record.User == user
    assert user.session == record


def test_authenticated_login(client: TestClient, user: User):
    post_data = {"user": user.Username, "passwd": "testPassword", "next": "/"}

    with client as request:
        # Try to login.
        response = request.post("/login", data=post_data, allow_redirects=False)
        assert response.status_code == int(HTTPStatus.SEE_OTHER)
        assert response.headers.get("location") == "/"

        # Now, let's verify that we get the logged in rendering
        # when requesting GET /login as an authenticated user.
        # Now, let's verify that we receive 403 Forbidden when we
        # try to get /login as an authenticated user.
        response = request.get(
            "/login", cookies=response.cookies, allow_redirects=False
        )
        assert response.status_code == int(HTTPStatus.OK)
        assert "Logged-in as: <strong>test</strong>" in response.text


def test_unauthenticated_logout_unauthorized(client: TestClient):
    with client as request:
        # Alright, let's verify that attempting to /logout when not
        # authenticated returns 401 Unauthorized.
        response = request.post("/logout", allow_redirects=False)
        assert response.status_code == int(HTTPStatus.SEE_OTHER)
        assert response.headers.get("location").startswith("/login")


def test_login_missing_username(client: TestClient):
    post_data = {"passwd": "testPassword", "next": "/"}

    with client as request:
        response = request.post("/login", data=post_data)
    assert "AURSID" not in response.cookies

    # Make sure password isn't prefilled and remember_me isn't checked.
    content = response.content.decode()
    assert post_data["passwd"] not in content
    assert "checked" not in content


def test_login_remember_me(client: TestClient, user: User):
    post_data = {
        "user": "test",
        "passwd": "testPassword",
        "next": "/",
        "remember_me": True,
    }

    with client as request:
        response = request.post("/login", data=post_data, allow_redirects=False)
    assert response.status_code == int(HTTPStatus.SEE_OTHER)
    assert "AURSID" in response.cookies

    cookie_timeout = aurweb.config.getint("options", "persistent_cookie_timeout")
    now_ts = time.utcnow()
    session = db.query(Session).filter(Session.UsersID == user.ID).first()

    # Expect that LastUpdateTS is not past the cookie timeout
    # for a remembered session.
    assert session.LastUpdateTS > (now_ts - cookie_timeout)


def test_login_incorrect_password_remember_me(client: TestClient, user: User):
    post_data = {
        "user": "test",
        "passwd": "badPassword",
        "next": "/",
        "remember_me": "on",
    }

    with client as request:
        response = request.post("/login", data=post_data)
    assert "AURSID" not in response.cookies

    # Make sure username is prefilled, password isn't prefilled,
    # and remember_me is checked.
    assert post_data["user"] in response.text
    assert post_data["passwd"] not in response.text
    assert "checked" in response.text


def test_login_missing_password(client: TestClient):
    post_data = {"user": "test", "next": "/"}

    with client as request:
        response = request.post("/login", data=post_data)
    assert "AURSID" not in response.cookies

    # Make sure username is prefilled and remember_me isn't checked.
    assert post_data["user"] in response.text
    assert "checked" not in response.text


def test_login_incorrect_password(client: TestClient):
    post_data = {"user": "test", "passwd": "badPassword", "next": "/"}

    with client as request:
        response = request.post("/login", data=post_data)
    assert "AURSID" not in response.cookies

    # Make sure username is prefilled, password isn't prefilled
    # and remember_me isn't checked.
    assert post_data["user"] in response.text
    assert post_data["passwd"] not in response.text
    assert "checked" not in response.text


def test_login_bad_referer(client: TestClient):
    post_data = {
        "user": "test",
        "passwd": "testPassword",
        "next": "/",
    }

    # Create new TestClient without a Referer header.
    client = TestClient(app)

    with client as request:
        response = request.post("/login", data=post_data)
    assert "AURSID" not in response.cookies

    BAD_REFERER = {
        "referer": aurweb.config.get("options", "aur_location") + ".mal.local",
    }
    with client as request:
        response = request.post("/login", data=post_data, headers=BAD_REFERER)
    assert response.status_code == int(HTTPStatus.BAD_REQUEST)
    assert "AURSID" not in response.cookies


def test_generate_unique_sid_exhausted(
    client: TestClient, user: User, caplog: pytest.LogCaptureFixture
):
    """
    In this test, we mock up generate_unique_sid() to infinitely return
    the same SessionID given to `user`. Within that mocking, we try
    to login as `user2` and expect the internal server error rendering
    by our error handler.

    This exercises the bad path of /login, where we can't find a unique
    SID to assign the user.
    """
    now = time.utcnow()
    with db.begin():
        # Create a second user; we'll login with this one.
        user2 = db.create(
            User,
            Username="test2",
            Email="test2@example.org",
            ResetKey="testReset",
            Passwd="testPassword",
            AccountTypeID=USER_ID,
        )

        # Create a session with ID == "testSession" for `user`.
        db.create(Session, User=user, SessionID="testSession", LastUpdateTS=now)

    # Mock out generate_unique_sid; always return "testSession" which
    # causes us to eventually error out and raise an internal error.
    def mock_generate_sid():
        return "testSession"

    # Login as `user2`; we expect an internal server error response
    # with a relevent detail.
    post_data = {
        "user": user2.Username,
        "passwd": "testPassword",
        "next": "/",
    }
    generate_unique_sid_ = "aurweb.models.session.generate_unique_sid"
    with mock.patch(generate_unique_sid_, mock_generate_sid):
        with client as request:
            # Set cookies = {} to remove any previous login kept by TestClient.
            response = request.post("/login", data=post_data, cookies={})
    assert response.status_code == int(HTTPStatus.INTERNAL_SERVER_ERROR)

    assert "500 - Internal Server Error" in response.text

    # Make sure an IntegrityError from the DB got logged out
    # with a FATAL traceback ID.
    expr = r"FATAL\[.{7}\]"
    assert re.search(expr, caplog.text)
    assert "IntegrityError" in caplog.text

    expr = r"Duplicate entry .+ for key .+SessionID.+"
    assert re.search(expr, response.text)
