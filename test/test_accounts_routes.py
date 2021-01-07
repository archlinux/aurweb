from http import HTTPStatus

import pytest

from fastapi.testclient import TestClient

from aurweb.asgi import app
from aurweb.db import query
from aurweb.models.account_type import AccountType
from aurweb.models.session import Session
from aurweb.models.user import User
from aurweb.testing import setup_test_db
from aurweb.testing.models import make_user
from aurweb.testing.requests import Request

# Some test global constants.
TEST_USERNAME = "test"
TEST_EMAIL = "test@example.org"

# Global mutables.
client = TestClient(app)
user = None


@pytest.fixture(autouse=True)
def setup():
    global user

    setup_test_db("Users", "Sessions", "Bans")

    account_type = query(AccountType,
                         AccountType.AccountType == "User").first()
    user = make_user(Username=TEST_USERNAME, Email=TEST_EMAIL,
                     RealName="Test User", Passwd="testPassword",
                     AccountType=account_type)


def test_get_passreset_authed_redirects():
    sid = user.login(Request(), "testPassword")
    assert sid is not None

    with client as request:
        response = request.get("/passreset", cookies={"AURSID": sid},
                               allow_redirects=False)

    assert response.status_code == int(HTTPStatus.SEE_OTHER)
    assert response.headers.get("location") == "/"


def test_get_passreset():
    with client as request:
        response = request.get("/passreset")
    assert response.status_code == int(HTTPStatus.OK)


def test_get_passreset_translation():
    # Test that translation works.
    with client as request:
        response = request.get("/passreset", cookies={"AURLANG": "de"})

    # The header title should be translated.
    assert "Passwort zurücksetzen".encode("utf-8") in response.content

    # The form input label should be translated.
    assert "Benutzername oder primäre E-Mail-Adresse eingeben:".encode(
        "utf-8") in response.content

    # And the button.
    assert "Weiter".encode("utf-8") in response.content


def test_get_passreset_with_resetkey():
    with client as request:
        response = request.get("/passreset", data={"resetkey": "abcd"})
    assert response.status_code == int(HTTPStatus.OK)


def test_post_passreset_authed_redirects():
    sid = user.login(Request(), "testPassword")
    assert sid is not None

    with client as request:
        response = request.post("/passreset",
                                cookies={"AURSID": sid},
                                data={"user": "blah"},
                                allow_redirects=False)

    assert response.status_code == int(HTTPStatus.SEE_OTHER)
    assert response.headers.get("location") == "/"


def test_post_passreset_user():
    # With username.
    with client as request:
        response = request.post("/passreset", data={"user": TEST_USERNAME})
    assert response.status_code == int(HTTPStatus.SEE_OTHER)
    assert response.headers.get("location") == "/passreset?step=confirm"

    # With e-mail.
    with client as request:
        response = request.post("/passreset", data={"user": TEST_EMAIL})
    assert response.status_code == int(HTTPStatus.SEE_OTHER)
    assert response.headers.get("location") == "/passreset?step=confirm"


def test_post_passreset_resetkey():
    from aurweb.db import session

    user.session = Session(UsersID=user.ID, SessionID="blah",
                           LastUpdateTS=datetime.utcnow().timestamp())
    session.commit()

    # Prepare a password reset.
    with client as request:
        response = request.post("/passreset", data={"user": TEST_USERNAME})
    assert response.status_code == int(HTTPStatus.SEE_OTHER)
    assert response.headers.get("location") == "/passreset?step=confirm"

    # Now that we've prepared the password reset, prepare a POST
    # request with the user's ResetKey.
    resetkey = user.ResetKey
    post_data = {
        "user": TEST_USERNAME,
        "resetkey": resetkey,
        "password": "abcd1234",
        "confirm": "abcd1234"
    }

    with client as request:
        response = request.post("/passreset", data=post_data)
    assert response.status_code == int(HTTPStatus.SEE_OTHER)
    assert response.headers.get("location") == "/passreset?step=complete"


def test_post_passreset_error_invalid_email():
    # First, test with a user that doesn't even exist.
    with client as request:
        response = request.post("/passreset", data={"user": "invalid"})
    assert response.status_code == int(HTTPStatus.NOT_FOUND)

    error = "Invalid e-mail."
    assert error in response.content.decode("utf-8")

    # Then, test with an invalid resetkey for a real user.
    _ = make_resetkey()
    post_data = make_passreset_data("fake")
    post_data["password"] = "abcd1234"
    post_data["confirm"] = "abcd1234"

    with client as request:
        response = request.post("/passreset", data=post_data)
    assert response.status_code == int(HTTPStatus.NOT_FOUND)
    assert error in response.content.decode("utf-8")


def make_resetkey():
    with client as request:
        response = request.post("/passreset", data={"user": TEST_USERNAME})
        assert response.status_code == int(HTTPStatus.SEE_OTHER)
        assert response.headers.get("location") == "/passreset?step=confirm"
    return user.ResetKey


def make_passreset_data(resetkey):
    return {
        "user": user.Username,
        "resetkey": resetkey
    }


def test_post_passreset_error_missing_field():
    # Now that we've prepared the password reset, prepare a POST
    # request with the user's ResetKey.
    resetkey = make_resetkey()
    post_data = make_passreset_data(resetkey)

    with client as request:
        response = request.post("/passreset", data=post_data)

    assert response.status_code == int(HTTPStatus.BAD_REQUEST)

    error = "Missing a required field."
    assert error in response.content.decode("utf-8")


def test_post_passreset_error_password_mismatch():
    resetkey = make_resetkey()
    post_data = make_passreset_data(resetkey)

    post_data["password"] = "abcd1234"
    post_data["confirm"] = "mismatched"

    with client as request:
        response = request.post("/passreset", data=post_data)

    assert response.status_code == int(HTTPStatus.BAD_REQUEST)

    error = "Password fields do not match."
    assert error in response.content.decode("utf-8")


def test_post_passreset_error_password_requirements():
    resetkey = make_resetkey()
    post_data = make_passreset_data(resetkey)

    passwd_min_len = User.minimum_passwd_length()
    assert passwd_min_len >= 4

    post_data["password"] = "x"
    post_data["confirm"] = "x"

    with client as request:
        response = request.post("/passreset", data=post_data)

    assert response.status_code == int(HTTPStatus.BAD_REQUEST)

    error = f"Your password must be at least {passwd_min_len} characters."
    assert error in response.content.decode("utf-8")
