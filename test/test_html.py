""" A test suite used to test HTML renders in different cases. """
from http import HTTPStatus

import pytest

from fastapi.testclient import TestClient

from aurweb import asgi, db
from aurweb.models.account_type import TRUSTED_USER_ID, USER_ID, AccountType
from aurweb.models.user import User
from aurweb.testing import setup_test_db
from aurweb.testing.html import get_errors, get_successes, parse_root
from aurweb.testing.requests import Request


@pytest.fixture(autouse=True)
def setup():
    setup_test_db(User.__tablename__)


@pytest.fixture
def client() -> TestClient:
    yield TestClient(app=asgi.app)


@pytest.fixture
def user() -> User:
    user_type = db.query(AccountType, AccountType.ID == USER_ID).first()
    with db.begin():
        user = db.create(User, Username="test", Email="test@example.org",
                         Passwd="testPassword", AccountType=user_type)
    yield user


@pytest.fixture
def trusted_user(user: User) -> User:
    tu_type = db.query(AccountType,
                       AccountType.ID == TRUSTED_USER_ID).first()
    with db.begin():
        user.AccountType = tu_type
    yield user


def test_archdev_navbar(client: TestClient):
    expected = [
        "AUR Home",
        "Packages",
        "Register",
        "Login"
    ]
    with client as request:
        resp = request.get("/")
    assert resp.status_code == int(HTTPStatus.OK)

    root = parse_root(resp.text)
    items = root.xpath('//div[@id="archdev-navbar"]/ul/li/a')
    for i, item in enumerate(items):
        assert item.text.strip() == expected[i]


def test_archdev_navbar_authenticated(client: TestClient, user: User):
    expected = [
        "Dashboard",
        "Packages",
        "Requests",
        "My Account",
        "Logout"
    ]
    cookies = {"AURSID": user.login(Request(), "testPassword")}
    with client as request:
        resp = request.get("/", cookies=cookies)
    assert resp.status_code == int(HTTPStatus.OK)

    root = parse_root(resp.text)
    items = root.xpath('//div[@id="archdev-navbar"]/ul/li/a')
    for i, item in enumerate(items):
        assert item.text.strip() == expected[i]


def test_archdev_navbar_authenticated_tu(client: TestClient,
                                         trusted_user: User):
    expected = [
        "Dashboard",
        "Packages",
        "Requests",
        "Accounts",
        "My Account",
        "Trusted User",
        "Logout"
    ]
    cookies = {"AURSID": trusted_user.login(Request(), "testPassword")}
    with client as request:
        resp = request.get("/", cookies=cookies)
    assert resp.status_code == int(HTTPStatus.OK)

    root = parse_root(resp.text)
    items = root.xpath('//div[@id="archdev-navbar"]/ul/li/a')
    for i, item in enumerate(items):
        assert item.text.strip() == expected[i]


def test_get_errors():
    html = """
    <ul class="errorlist">
        <li>Test</li>
    </ul>
"""
    errors = get_errors(html)
    assert errors[0].text.strip() == "Test"


def test_get_successes():
    html = """
    <ul class="success">
        <li>Test</li>
    </ul>
"""
    successes = get_successes(html)
    assert successes[0].text.strip() == "Test"


def test_metrics(client: TestClient):
    with client as request:
        resp = request.get("/metrics")
    assert resp.status_code == int(HTTPStatus.OK)
    assert resp.headers.get("Content-Type").startswith("text/plain")
