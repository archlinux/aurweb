import re
from http import HTTPStatus
from unittest import mock

import lxml.etree
import pytest
from fastapi.testclient import TestClient

from aurweb import aur_logging, db, time
from aurweb.asgi import app
from aurweb.models.account_type import AccountType
from aurweb.models.package import Package
from aurweb.models.package_base import PackageBase
from aurweb.models.user import User

logger = aur_logging.get_logger(__name__)


@pytest.fixture(autouse=True)
def setup(db_test):
    return


@pytest.fixture
def client():
    yield TestClient(app=app)


@pytest.fixture
def user():
    account_type = db.query(AccountType, AccountType.AccountType == "User").first()
    yield db.create(
        User,
        Username="test",
        Email="test@example.org",
        RealName="Test User",
        Passwd="testPassword",
        AccountType=account_type,
    )


@pytest.fixture
def packages(user):
    pkgs = []
    now = time.utcnow()

    # Create 101 packages; we limit 100 on RSS feeds.
    with db.begin():
        for i in range(101):
            pkgbase = db.create(
                PackageBase,
                Maintainer=user,
                Name=f"test-package-{i}",
                SubmittedTS=(now + i),
                ModifiedTS=(now + i),
            )
            pkg = db.create(Package, Name=pkgbase.Name, PackageBase=pkgbase)
            pkgs.append(pkg)
    yield pkgs


def parse_root(xml):
    return lxml.etree.fromstring(xml)


def test_rss(client, user, packages):
    with client as request:
        response = request.get("/rss/")
    assert response.status_code == int(HTTPStatus.OK)

    # Test that the RSS we got is sorted by descending SubmittedTS.
    def key_(pkg):
        return pkg.PackageBase.SubmittedTS

    packages = sorted(packages, key=key_, reverse=True)

    # Just take the first 100.
    packages = packages[:100]

    root = parse_root(response.content)
    items = root.xpath("//channel/item")
    assert len(items) == 100

    for i, item in enumerate(items):
        title = next(iter(item.xpath("./title")))
        logger.debug("title: '%s' vs name: '%s'", title.text, packages[i].Name)
        assert title.text == packages[i].Name


def test_rss_modified(client, user, packages):
    with client as request:
        response = request.get("/rss/modified")
    assert response.status_code == int(HTTPStatus.OK)

    # Test that the RSS we got is sorted by descending SubmittedTS.
    def key_(pkg):
        return pkg.PackageBase.ModifiedTS

    packages = sorted(packages, key=key_, reverse=True)

    # Just take the first 100.
    packages = packages[:100]

    root = parse_root(response.content)
    items = root.xpath("//channel/item")
    assert len(items) == 100

    for i, item in enumerate(items):
        title = next(iter(item.xpath("./title")))
        logger.debug("title: '%s' vs name: '%s'", title.text, packages[i].Name)
        assert title.text == packages[i].Name


def test_rss_cache_headers(client, user, packages):
    """Test that the RSS feed endpoint returns the expected cache headers."""
    with client as request:
        response = request.get("/rss/")

    # Check status code
    assert response.status_code == int(HTTPStatus.OK)

    # Check that necessary cache headers are present
    assert "Cache-Control" in response.headers
    assert "ETag" in response.headers
    assert "Last-Modified" in response.headers

    # Check Cache-Control header format
    cache_control = response.headers["Cache-Control"]
    assert "public" in cache_control
    assert "max-age=" in cache_control

    # Extract max-age value and check it's a positive number
    max_age_match = re.search(r"max-age=(\d+)", cache_control)
    assert max_age_match
    max_age = int(max_age_match.group(1))
    assert max_age > 0

    # Check ETag format (should be in quotes)
    etag = response.headers["ETag"]
    assert etag.startswith('"') and etag.endswith('"')

    # Check Last-Modified format (should be in HTTP date format)
    last_modified = response.headers["Last-Modified"]
    # RFC 7232 compliant date format: "EEE, dd MMM yyyy HH:mm:ss 'GMT'"
    http_date_pattern = r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}[+-]\d{4}$"
    assert re.match(http_date_pattern, last_modified)


def test_rss_modified_cache_headers(client, user, packages):
    """Test that the RSS modified feed endpoint returns the expected cache headers."""
    with client as request:
        response = request.get("/rss/modified")

    # Check status code
    assert response.status_code == int(HTTPStatus.OK)

    # Check that necessary cache headers are present
    assert "Cache-Control" in response.headers
    assert "ETag" in response.headers
    assert "Last-Modified" in response.headers

    # Check Cache-Control header format
    cache_control = response.headers["Cache-Control"]
    assert "public" in cache_control
    assert "max-age=" in cache_control


def test_etag_consistency(client, user, packages):
    """Test that the ETag is consistent for the same content."""
    with client as request:
        response1 = request.get("/rss/")
        etag1 = response1.headers["ETag"]

        # Make a second request immediately, should return the same ETag
        response2 = request.get("/rss/")
        etag2 = response2.headers["ETag"]

    # ETags should be the same for both responses
    assert etag1 == etag2


def test_conditional_request(client, user, packages):
    """Test conditional requests with If-None-Match header."""
    with client as request:
        # Make an initial request to get the ETag
        response1 = request.get("/rss/")
        etag = response1.headers["ETag"]

        # Make a second request with If-None-Match header
        response2 = request.get("/rss/", headers={"If-None-Match": etag})

    # Should return 304 Not Modified
    assert response2.status_code == 304


def test_cache_expiry(client, user, packages):
    """Test that the cache headers are updated after cache expiry."""
    # This test uses mock to simulate time passing
    with mock.patch("time.time") as mock_time:
        # Set initial time
        initial_time = time.utcnow()
        mock_time.return_value = initial_time

        with client as request:
            # First request
            response1 = request.get("/rss/")
            etag1 = response1.headers["ETag"]

            # Advance time beyond cache expiry (e.g., 6 minutes later)
            mock_time.return_value = initial_time + 360  # 6 minutes in seconds

            # Second request after cache should have expired
            response2 = request.get("/rss/")
            etag2 = response2.headers["ETag"]

    # ETags should be different after cache expiry
    assert etag1 != etag2
