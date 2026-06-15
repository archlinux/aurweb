from http import HTTPStatus
from typing import Generator

import pytest
from fastapi.testclient import TestClient

import aurweb.config
from aurweb import db, time
from aurweb.asgi import app
from aurweb.db import create
from aurweb.git import serve
from aurweb.models.account_type import USER_ID
from aurweb.models.user import User
from aurweb.testing.requests import Request
from aurweb.users import update, verify

TEST_REFERER = {
    "referer": aurweb.config.get("options", "aur_location") + "/login",
}


@pytest.fixture(autouse=True)
def setup(db_test):
    return


@pytest.fixture
def client() -> TestClient:
    client = TestClient(app=app)
    client.headers.update(TEST_REFERER)
    client.follow_redirects = False
    yield client


def create_user(username: str, **kwargs) -> User:
    with db.begin():
        user = create(
            User,
            Username=username,
            Email=f"{username}@example.org",
            Passwd="testPassword",
            AccountTypeID=USER_ID,
            **kwargs,
        )
    return user


@pytest.fixture
def user() -> Generator[User]:
    yield create_user("verifyuser")


@pytest.fixture
def other() -> Generator[User]:
    yield create_user("otheruser")


def test_issue_sets_token_and_expiry(user: User):
    before = time.utcnow()
    with db.begin():
        verify.issue(user)

    assert user.EmailVerificationToken is not None
    assert len(user.EmailVerificationToken) == 32
    # Expiry should be ~ now + TTL.
    assert abs(user.EmailVerificationExpiry - (before + verify.TTL)) < 5


def test_in_cooldown(user: User):
    # No token -> not in cooldown.
    assert verify.in_cooldown(user) is False

    # Freshly issued -> in cooldown.
    with db.begin():
        verify.issue(user)
    assert verify.in_cooldown(user) is True

    # Issued long ago -> out of cooldown (but not yet expired).
    with db.begin():
        user.EmailVerificationExpiry = time.utcnow() + verify.TTL - verify.COOLDOWN - 60
    assert verify.in_cooldown(user) is False


def test_is_expired(user: User):
    # No token -> treated as expired.
    assert verify.is_expired(user) is True

    with db.begin():
        verify.issue(user)
    assert verify.is_expired(user) is False

    with db.begin():
        user.EmailVerificationExpiry = time.utcnow() - 10
    assert verify.is_expired(user) is True


def post_register(request, **kwargs):
    from aurweb import captcha

    salt = captcha.get_captcha_salts()[0]
    token = captcha.get_captcha_token(salt)
    answer = captcha.get_captcha_answer(token)
    data = {
        "U": "newUser",
        "E": "newUser@email.org",
        "P": "newUserPassword",
        "C": "newUserPassword",
        "L": "en",
        "TZ": "UTC",
        "captcha": answer,
        "captcha_salt": salt,
    }
    data.update(kwargs)
    return request.post("/register", data=data)


def test_register_starts_unverified_with_token(client: TestClient):
    with client as request:
        response = post_register(request)
    assert response.status_code == int(HTTPStatus.OK)

    new = db.query(User).filter(User.Username == "newUser").first()
    assert new is not None
    assert not new.EmailVerified
    assert new.EmailVerificationToken is not None
    assert new.EmailVerificationExpiry is not None


def test_verify_status_page(client: TestClient):
    with client as request:
        response = request.get("/account/verify", params={"step": "confirm"})
    assert response.status_code == int(HTTPStatus.OK)
    assert "check your e-mail" in response.content.decode().lower()


def test_verify_route_valid_token(client: TestClient, user: User):
    with db.begin():
        verify.issue(user)
    token = user.EmailVerificationToken

    with client as request:
        response = request.get(f"/account/verify/{token}")
    # POST/redirect/GET -> redirect to the status page.
    assert response.status_code == int(HTTPStatus.SEE_OTHER)
    assert "step=complete" in response.headers["location"]

    user = db.refresh(user)
    assert user.EmailVerified
    assert user.EmailVerificationToken is None
    assert user.EmailVerificationExpiry is None


def test_verify_route_expired_token(client: TestClient, user: User):
    with db.begin():
        verify.issue(user)
        user.EmailVerificationExpiry = time.utcnow() - 10
    token = user.EmailVerificationToken

    with client as request:
        response = request.get(f"/account/verify/{token}")
    assert response.status_code == int(HTTPStatus.SEE_OTHER)
    assert "step=invalid" in response.headers["location"]

    user = db.refresh(user)
    assert not user.EmailVerified


def test_verify_route_unknown_token(client: TestClient):
    with client as request:
        response = request.get("/account/verify/" + "0" * 32)
    assert response.status_code == int(HTTPStatus.SEE_OTHER)
    assert "step=invalid" in response.headers["location"]


def test_verify_route_already_verified(client: TestClient, user: User):
    with db.begin():
        verify.issue(user)
        user.EmailVerified = True
    token = user.EmailVerificationToken

    with client as request:
        response = request.get(f"/account/verify/{token}")
    assert response.status_code == int(HTTPStatus.SEE_OTHER)
    assert "step=already" in response.headers["location"]


def test_resend_sends_when_unverified(client: TestClient, user: User):
    sid = user.login(Request(), "testPassword")
    with client as request:
        request.cookies = {"AURSID": sid}
        response = request.post(f"/account/{user.Username}/verify")
    assert response.status_code == int(HTTPStatus.SEE_OTHER)
    assert "step=confirm" in response.headers["location"]

    user = db.refresh(user)
    assert user.EmailVerificationToken is not None


def test_resend_respects_cooldown(client: TestClient, user: User):
    with db.begin():
        verify.issue(user)  # fresh token => in cooldown

    sid = user.login(Request(), "testPassword")
    with client as request:
        request.cookies = {"AURSID": sid}
        response = request.post(f"/account/{user.Username}/verify")
    assert response.status_code == int(HTTPStatus.SEE_OTHER)
    assert "step=cooldown" in response.headers["location"]


def test_resend_already_verified(client: TestClient, user: User):
    with db.begin():
        user.EmailVerified = True

    sid = user.login(Request(), "testPassword")
    with client as request:
        request.cookies = {"AURSID": sid}
        response = request.post(f"/account/{user.Username}/verify")
    assert response.status_code == int(HTTPStatus.SEE_OTHER)
    assert "step=already" in response.headers["location"]


def test_resend_unauthorized_for_other_user(
    client: TestClient, user: User, other: User
):
    # `other` is logged in but targets `user`'s account -> not permitted.
    sid = other.login(Request(), "testPassword")
    with client as request:
        request.cookies = {"AURSID": sid}
        response = request.post(f"/account/{user.Username}/verify")
    assert response.status_code == int(HTTPStatus.SEE_OTHER)
    assert "step=" not in response.headers["location"]


def test_email_change_resets_verification(user: User):
    with db.begin():
        user.EmailVerified = True

    update.simple(E="changed@example.org", user=user)

    user = db.refresh(user)
    assert not user.EmailVerified
    assert user.EmailVerificationToken is not None
    assert user.Email == "changed@example.org"


def test_unchanged_email_keeps_verification(user: User):
    with db.begin():
        user.EmailVerified = True

    update.simple(E=user.Email, user=user)

    user = db.refresh(user)
    assert user.EmailVerified


def test_user_email_verified_helper(user: User, other: User):
    with db.begin():
        user.EmailVerified = True
        other.EmailVerified = False

    assert serve.user_email_verified(user.Username) is True
    assert serve.user_email_verified(other.Username) is False
    assert serve.user_email_verified("nonexistent-user") is False
