from datetime import datetime
from http import HTTPStatus

import pytest

from fastapi.testclient import TestClient

import aurweb.config

from aurweb.asgi import app
from aurweb.db import create, query
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


def test_login_missing_password():
    post_data = {
        "user": "test",
        "next": "/"
    }

    with client as request:
        response = request.post("/login", data=post_data)
    assert "AURSID" not in response.cookies


def test_login_incorrect_password():
    post_data = {
        "user": "test",
        "passwd": "badPassword",
        "next": "/"
    }

    with client as request:
        response = request.post("/login", data=post_data)
    assert "AURSID" not in response.cookies
