from datetime import datetime
from http import HTTPStatus
from unittest import mock

import pytest

from fastapi.testclient import TestClient

import aurweb.config

from aurweb.asgi import app
from aurweb.db import begin, create, query
from aurweb.models.account_type import AccountType
from aurweb.models.session import Session
from aurweb.models.user import User
from aurweb.testing import setup_test_db

# Some test global constants.
TEST_USERNAME = "test"
TEST_EMAIL = "test@example.org"

# Global mutables.
user = client = None


@pytest.fixture(autouse=True)
def setup():
    global user, client

    setup_test_db("Users", "Sessions", "Bans")

    account_type = query(AccountType,
                         AccountType.AccountType == "User").first()

    with begin():
        user = create(User, Username=TEST_USERNAME, Email=TEST_EMAIL,
                      RealName="Test User", Passwd="testPassword",
                      AccountType=account_type)

    client = TestClient(app)


def test_login_logout():
    post_data = {
        "user": "test",
        "passwd": "testPassword",
        "next": "/"
    }

    with client as request:
        # First, let's test get /login.
        response = request.get("/login")
        assert response.status_code == int(HTTPStatus.OK)

        response = request.post("/login", data=post_data,
                                allow_redirects=False)
        assert response.status_code == int(HTTPStatus.SEE_OTHER)

        # Simulate following the redirect location from above's response.
        response = request.get(response.headers.get("location"))
        assert response.status_code == int(HTTPStatus.OK)

        response = request.post("/logout", data=post_data,
                                allow_redirects=False)
        assert response.status_code == int(HTTPStatus.SEE_OTHER)

        response = request.post("/logout", data=post_data, cookies={
            "AURSID": response.cookies.get("AURSID")
        }, allow_redirects=False)
        assert response.status_code == int(HTTPStatus.SEE_OTHER)

    assert "AURSID" not in response.cookies


def mock_getboolean(a, b):
    if a == "options" and b == "disable_http_login":
        return True
    return bool(aurweb.config.get(a, b))


@mock.patch("aurweb.config.getboolean", side_effect=mock_getboolean)
def test_secure_login(mock):
    """ In this test, we check to verify the course of action taken
    by starlette when providing secure=True to a response cookie.
    This is achieved by mocking aurweb.config.getboolean to return
    True (or 1) when looking for `options.disable_http_login`.
    When we receive a response with `disable_http_login` enabled,
    we check the fields in cookies received for the secure and
    httponly fields, in addition to the rest of the fields given
    on such a request. """

    # Create a local TestClient here since we mocked configuration.
    client = TestClient(app)

    # Data used for our upcoming http post request.
    post_data = {
        "user": user.Username,
        "passwd": "testPassword",
        "next": "/"
    }

    # Perform a login request with the data matching our user.
    with client as request:
        response = request.post("/login", data=post_data,
                                allow_redirects=False)

    # Make sure we got the expected status out of it.
    assert response.status_code == int(HTTPStatus.SEE_OTHER)

    # Let's check what we got in terms of cookies for AURSID.
    # Make sure that a secure cookie got passed to us.
    cookie = next(c for c in response.cookies if c.name == "AURSID")
    assert cookie.secure is True
    assert cookie.has_nonstandard_attr("HttpOnly") is True
    assert cookie.has_nonstandard_attr("SameSite") is True
    assert cookie.get_nonstandard_attr("SameSite") == "strict"
    assert cookie.value is not None and len(cookie.value) > 0

    # Let's make sure we actually have a session relationship
    # with the AURSID we ended up with.
    record = query(Session, Session.SessionID == cookie.value).first()
    assert record is not None and record.User == user
    assert user.session == record


def test_authenticated_login_forbidden():
    post_data = {
        "user": "test",
        "passwd": "testPassword",
        "next": "/"
    }

    with client as request:
        # Login.
        response = request.post("/login", data=post_data,
                                allow_redirects=False)
        assert response.status_code == int(HTTPStatus.SEE_OTHER)

        # Now, let's verify that we receive 403 Forbidden when we
        # try to get /login as an authenticated user.
        response = request.get("/login", allow_redirects=False)
        assert response.status_code == int(HTTPStatus.SEE_OTHER)


def test_unauthenticated_logout_unauthorized():
    with client as request:
        # Alright, let's verify that attempting to /logout when not
        # authenticated returns 401 Unauthorized.
        response = request.get("/logout", allow_redirects=False)
        assert response.status_code == int(HTTPStatus.SEE_OTHER)


def test_login_missing_username():
    post_data = {
        "passwd": "testPassword",
        "next": "/"
    }

    with client as request:
        response = request.post("/login", data=post_data)
    assert "AURSID" not in response.cookies

    # Make sure password isn't prefilled and remember_me isn't checked.
    content = response.content.decode()
    assert post_data["passwd"] not in content
    assert "checked" not in content


def test_login_remember_me():
    post_data = {
        "user": "test",
        "passwd": "testPassword",
        "next": "/",
        "remember_me": True
    }

    with client as request:
        response = request.post("/login", data=post_data,
                                allow_redirects=False)
    assert response.status_code == int(HTTPStatus.SEE_OTHER)
    assert "AURSID" in response.cookies

    cookie_timeout = aurweb.config.getint(
        "options", "persistent_cookie_timeout")
    expected_ts = datetime.utcnow().timestamp() + cookie_timeout

    _session = query(Session,
                     Session.UsersID == user.ID).first()

    # Expect that LastUpdateTS was within 5 seconds of the expected_ts,
    # which is equal to the current timestamp + persistent_cookie_timeout.
    assert _session.LastUpdateTS > expected_ts - 5
    assert _session.LastUpdateTS < expected_ts + 5


def test_login_incorrect_password_remember_me():
    post_data = {
        "user": "test",
        "passwd": "badPassword",
        "next": "/",
        "remember_me": "on"
    }

    with client as request:
        response = request.post("/login", data=post_data)
    assert "AURSID" not in response.cookies

    # Make sure username is prefilled, password isn't prefilled, and remember_me
    # is checked.
    content = response.content.decode()
    assert post_data["user"] in content
    assert post_data["passwd"] not in content
    assert "checked" in content


def test_login_missing_password():
    post_data = {
        "user": "test",
        "next": "/"
    }

    with client as request:
        response = request.post("/login", data=post_data)
    assert "AURSID" not in response.cookies

    # Make sure username is prefilled and remember_me isn't checked.
    content = response.content.decode()
    assert post_data["user"] in content
    assert "checked" not in content


def test_login_incorrect_password():
    post_data = {
        "user": "test",
        "passwd": "badPassword",
        "next": "/"
    }

    with client as request:
        response = request.post("/login", data=post_data)
    assert "AURSID" not in response.cookies

    # Make sure username is prefilled, password isn't prefilled and remember_me
    # isn't checked.
    content = response.content.decode()
    assert post_data["user"] in content
    assert post_data["passwd"] not in content
    assert "checked" not in content
