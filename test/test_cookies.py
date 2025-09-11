from datetime import datetime
from http import HTTPStatus
from typing import Generator

import pytest
from fastapi.testclient import TestClient

from aurweb import config, db
from aurweb.asgi import app
from aurweb.models.account_type import USER_ID
from aurweb.models.user import User
from aurweb.testing.requests import Request

# Some test global constants.
TEST_USERNAME = "test"
TEST_EMAIL = "test@example.org"
TEST_REFERER = {
    "referer": config.get("options", "aur_location") + "/login",
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

    # disable redirects for our tests
    client.follow_redirects = False
    yield client


@pytest.fixture
def user() -> Generator[User]:
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


def test_cookies_login(client: TestClient, user: User):
    # Log in with "Remember me" disabled
    data = {"user": user.Username, "passwd": "testPassword", "next": "/"}
    with client as request:
        resp = request.post("/login", data=data)

    local_time = int(datetime.now().timestamp())
    expected_permanent = local_time + config.getint(
        "options", "permanent_cookie_timeout"
    )

    # Check if we got permanent cookies with expected expiry date.
    # Allow 1 second difference to account for timing issues
    # between the request and current time.
    # AURSID should be a session cookie (no expiry date)
    assert "AURSID", "AURREMEMBER" in resp.cookies
    for cookie in resp.cookies.jar:
        if cookie.name == "AURSID":
            assert cookie.expires is None

        if cookie.name == "AURREMEMBER":
            assert abs(cookie.expires - expected_permanent) < 2
            assert cookie.value == "False"

    # Log out
    with client as request:
        request.cookies = resp.cookies
        resp = request.post("/logout", data=data)

    # Make sure AURSID cookie is removed after logout
    assert "AURSID" not in resp.cookies

    # Log in with "Remember me" enabled
    data = {
        "user": user.Username,
        "passwd": "testPassword",
        "next": "/",
        "remember_me": "True",
    }
    with client as request:
        resp = request.post("/login", data=data)

    # Check if we got a permanent cookie with expected expiry date.
    # Allow 1 second difference to account for timing issues
    # between the request and current time.
    # AURSID should be a persistent cookie
    expected_persistent = local_time + config.getint(
        "options", "persistent_cookie_timeout"
    )
    assert "AURSID", "AURREMEMBER" in resp.cookies
    for cookie in resp.cookies.jar:
        if cookie.name in "AURSID":
            assert abs(cookie.expires - expected_persistent) < 2

        if cookie.name == "AURREMEMBER":
            assert abs(cookie.expires - expected_permanent) < 2
            assert cookie.value == "True"

    # log in again even though we already have a session
    with client as request:
        resp = request.post("/login", data=data)

    # we are logged in already and should have been redirected
    assert resp.status_code == int(HTTPStatus.SEE_OTHER)
    assert resp.headers.get("location") == "/"


def test_cookie_language(client: TestClient, user: User):
    # Unauthenticated reqeuests should set AURLANG cookie
    data = {"set_lang": "en", "next": "/"}
    with client as request:
        resp = request.post("/language", data=data)

    local_time = int(datetime.now().timestamp())
    expected_permanent = local_time + config.getint(
        "options", "permanent_cookie_timeout"
    )

    # Make sure we got an AURLANG cookie
    assert "AURLANG" in resp.cookies
    assert resp.cookies.get("AURLANG") == "en"

    # Check if we got a permanent cookie with expected expiry date.
    # Allow 1 second difference to account for timing issues
    # between the request and current time.
    for cookie in resp.cookies.jar:
        if cookie.name in "AURLANG":
            assert abs(cookie.expires - expected_permanent) < 2

    # Login and change the language
    # We should not get a cookie since we store
    # our language setting in the DB anyways
    sid = user.login(Request(), "testPassword")
    data = {"set_lang": "en", "next": "/"}
    with client as request:
        request.cookies = {"AURSID": sid}
        resp = request.post("/language", data=data)

    assert "AURLANG" not in resp.cookies
