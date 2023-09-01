""" A test suite used to test HTML renders in different cases. """
import hashlib
import os
import tempfile
from http import HTTPStatus
from unittest import mock

import fastapi
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from aurweb import asgi, config, db
from aurweb.models import PackageBase
from aurweb.models.account_type import PACKAGE_MAINTAINER_ID, USER_ID
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
        user = db.create(
            User,
            Username="test",
            Email="test@example.org",
            Passwd="testPassword",
            AccountTypeID=USER_ID,
        )
    yield user


@pytest.fixture
def package_maintainer(user: User) -> User:
    with db.begin():
        user.AccountTypeID = PACKAGE_MAINTAINER_ID
    yield user


@pytest.fixture
def pkgbase(user: User) -> PackageBase:
    with db.begin():
        pkgbase = db.create(PackageBase, Name="test-pkg", Maintainer=user)
    yield pkgbase


def test_archdev_navbar(client: TestClient):
    expected = ["AUR Home", "Packages", "Register", "Login"]
    with client as request:
        resp = request.get("/")
    assert resp.status_code == int(HTTPStatus.OK)

    root = parse_root(resp.text)
    items = root.xpath('//div[@id="archdev-navbar"]/ul/li/a')
    for i, item in enumerate(items):
        assert item.text.strip() == expected[i]


def test_archdev_navbar_authenticated(client: TestClient, user: User):
    expected = ["Dashboard", "Packages", "Requests", "My Account", "Logout"]
    cookies = {"AURSID": user.login(Request(), "testPassword")}
    with client as request:
        request.cookies = cookies
        resp = request.get("/")
    assert resp.status_code == int(HTTPStatus.OK)

    root = parse_root(resp.text)
    items = root.xpath('//div[@id="archdev-navbar"]/ul/li/a')
    for i, item in enumerate(items):
        assert item.text.strip() == expected[i]


def test_archdev_navbar_authenticated_tu(client: TestClient, package_maintainer: User):
    expected = [
        "Dashboard",
        "Packages",
        "Requests",
        "Accounts",
        "My Account",
        "Trusted User",
        "Logout",
    ]
    cookies = {"AURSID": package_maintainer.login(Request(), "testPassword")}
    with client as request:
        request.cookies = cookies
        resp = request.get("/")
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


def test_archive_sig(client: TestClient):
    hash_value = hashlib.sha256(b"test").hexdigest()

    with tempfile.TemporaryDirectory() as tmpdir:
        packages_sha256 = os.path.join(tmpdir, "packages.gz.sha256")
        with open(packages_sha256, "w") as f:
            f.write(hash_value)

        config_get = config.get

        def mock_config(section: str, key: str):
            if key == "archivedir":
                return tmpdir
            return config_get(section, key)

        with mock.patch("aurweb.config.get", side_effect=mock_config):
            with client as request:
                resp = request.get("/packages.gz.sha256")

    assert resp.status_code == int(HTTPStatus.OK)
    assert resp.text == hash_value


def test_archive_sig_404(client: TestClient):
    with client as request:
        resp = request.get("/blah.gz.sha256")
    assert resp.status_code == int(HTTPStatus.NOT_FOUND)


def test_metrics(client: TestClient):
    with tempfile.TemporaryDirectory() as tmpdir:
        env = {"PROMETHEUS_MULTIPROC_DIR": tmpdir}
        with mock.patch.dict(os.environ, env):
            with client as request:
                resp = request.get("/metrics")
    assert resp.status_code == int(HTTPStatus.OK)
    assert resp.headers.get("Content-Type").startswith("text/plain")


def test_disabled_metrics(client: TestClient):
    env = {"PROMETHEUS_MULTIPROC_DIR": str()}
    with mock.patch.dict(os.environ, env):
        with client as request:
            resp = request.get("/metrics")
    assert resp.status_code == int(HTTPStatus.SERVICE_UNAVAILABLE)


def test_rtl(client: TestClient):
    responses = {}
    expected = [[], [], ["rtl"], ["rtl"]]
    with client as request:
        responses["default"] = request.get("/")
        request.cookies = {"AURLANG": "de"}
        responses["de"] = request.get("/")
        request.cookies = {"AURLANG": "he"}
        responses["he"] = request.get("/")
        request.cookies = {"AURLANG": "ar"}
        responses["ar"] = request.get("/")
    for i, (lang, resp) in enumerate(responses.items()):
        assert resp.status_code == int(HTTPStatus.OK)
        t = parse_root(resp.text)
        assert t.xpath("//html/@dir") == expected[i]


def test_404_with_valid_pkgbase(client: TestClient, pkgbase: PackageBase):
    """Test HTTPException with status_code == 404 and valid pkgbase."""
    endpoint = f"/{pkgbase.Name}"
    with client as request:
        response = request.get(endpoint)
    assert response.status_code == int(HTTPStatus.NOT_FOUND)

    body = response.text
    assert "404 - Page Not Found" in body
    assert "To clone the Git repository" in body


def test_404(client: TestClient):
    """Test HTTPException with status_code == 404 without a valid pkgbase."""
    with client as request:
        response = request.get("/nonexistentroute")
    assert response.status_code == int(HTTPStatus.NOT_FOUND)

    body = response.text
    assert "404 - Page Not Found" in body
    # No `pkgbase` is provided here; we don't see the extra info.
    assert "To clone the Git repository" not in body


def test_503(client: TestClient):
    """Test HTTPException with status_code == 503 (Service Unavailable)."""

    @asgi.app.get("/raise-503")
    async def raise_503(request: fastapi.Request):
        raise HTTPException(status_code=HTTPStatus.SERVICE_UNAVAILABLE)

    with TestClient(app=asgi.app) as request:
        response = request.get("/raise-503")
    assert response.status_code == int(HTTPStatus.SERVICE_UNAVAILABLE)
