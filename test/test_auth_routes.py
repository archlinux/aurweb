from datetime import datetime
from http import HTTPStatus

import pytest

from fastapi.testclient import TestClient

import aurweb.config

from aurweb.asgi import app
from aurweb.db import query
from aurweb.models.account_type import AccountType
from aurweb.models.session import Session
from aurweb.testing import setup_test_db
from aurweb.testing.models import make_user

client = TestClient(app)

user = None


@pytest.fixture(autouse=True)
def setup():
    global user

    setup_test_db("Users", "Sessions", "Bans")

    account_type = query(AccountType,
                         AccountType.AccountType == "User").first()
    user = make_user(Username="test", Email="test@example.org",
                     RealName="Test User", Passwd="testPassword",
                     AccountType=account_type)


def test_login_logout():
    post_data = {
        "user": "test",
        "passwd": "testPassword",
        "next": "/"
    }

    with client as request:
        response = client.get("/login")
        assert response.status_code == int(HTTPStatus.OK)

        response = request.post("/login", data=post_data,
                                allow_redirects=False)
        assert response.status_code == int(HTTPStatus.SEE_OTHER)

        response = request.get(response.headers.get("location"), cookies={
            "AURSID": response.cookies.get("AURSID")
        })
        assert response.status_code == int(HTTPStatus.OK)

        response = request.post("/logout", data=post_data,
                                allow_redirects=False)
        assert response.status_code == int(HTTPStatus.SEE_OTHER)

        response = request.post("/logout", data=post_data, cookies={
            "AURSID": response.cookies.get("AURSID")
        }, allow_redirects=False)
        assert response.status_code == int(HTTPStatus.SEE_OTHER)
    assert "AURSID" not in response.cookies


def test_login_missing_username():
    post_data = {
        "passwd": "testPassword",
        "next": "/"
    }

    with client as request:
        response = request.post("/login", data=post_data)
    assert "AURSID" not in response.cookies


def test_login_remember_me():
    from aurweb.db import session

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

    _session = session.query(Session).filter(
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
