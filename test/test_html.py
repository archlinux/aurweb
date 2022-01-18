""" A test suite used to test HTML renders in different cases. """
from http import HTTPStatus

import fastapi
import pytest

from fastapi import HTTPException
from fastapi.testclient import TestClient

from aurweb import asgi, db
from aurweb.models import PackageBase
from aurweb.models.account_type import TRUSTED_USER_ID, USER_ID
from aurweb.models.user import User
from aurweb.testing.html import get_errors, get_successes, parse_root
from aurweb.testing.requests import Request


@pytest.fixture(autouse=True)
def setup(db_test):
    return


@pytest.fixture
def client() -> TestClient:
    yield TestClient(app=asgi.app)


@pytest.fixture
def user() -> User:
    with db.begin():
        user = db.create(User, Username="test", Email="test@example.org",
                         Passwd="testPassword", AccountTypeID=USER_ID)
    yield user


@pytest.fixture
def trusted_user(user: User) -> User:
    with db.begin():
        user.AccountTypeID = TRUSTED_USER_ID
    yield user


@pytest.fixture
def pkgbase(user: User) -> PackageBase:
    with db.begin():
        pkgbase = db.create(PackageBase, Name="test-pkg", Maintainer=user)
    yield pkgbase


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


def test_404_with_valid_pkgbase(client: TestClient, pkgbase: PackageBase):
    """ Test HTTPException with status_code == 404 and valid pkgbase. """
    endpoint = f"/{pkgbase.Name}"
    with client as request:
        response = request.get(endpoint)
    assert response.status_code == int(HTTPStatus.NOT_FOUND)

    body = response.text
    assert "404 - Page Not Found" in body
    assert "To clone the Git repository" in body


def test_404(client: TestClient):
    """ Test HTTPException with status_code == 404 without a valid pkgbase. """
    with client as request:
        response = request.get("/nonexistentroute")
    assert response.status_code == int(HTTPStatus.NOT_FOUND)

    body = response.text
    assert "404 - Page Not Found" in body
    # No `pkgbase` is provided here; we don't see the extra info.
    assert "To clone the Git repository" not in body


def test_503(client: TestClient):
    """ Test HTTPException with status_code == 503 (Service Unavailable). """
    @asgi.app.get("/raise-503")
    async def raise_503(request: fastapi.Request):
        raise HTTPException(status_code=HTTPStatus.SERVICE_UNAVAILABLE)

    with TestClient(app=asgi.app) as request:
        response = request.get("/raise-503")
    assert response.status_code == int(HTTPStatus.SERVICE_UNAVAILABLE)
