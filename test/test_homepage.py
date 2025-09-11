import re
from http import HTTPStatus
from typing import Generator
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from aurweb import db, time
from aurweb.asgi import app
from aurweb.aur_redis import redis_connection
from aurweb.models.account_type import USER_ID
from aurweb.models.package import Package
from aurweb.models.package_base import PackageBase
from aurweb.models.package_comaintainer import PackageComaintainer
from aurweb.models.package_request import PackageRequest
from aurweb.models.request_type import DELETION_ID, RequestType
from aurweb.models.user import User
from aurweb.testing.html import parse_root
from aurweb.testing.requests import Request

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup(db_test):
    return


@pytest.fixture
def user():
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
def user2():
    with db.begin():
        user = db.create(
            User,
            Username="test2",
            Email="test2@example.org",
            Passwd="testPassword",
            AccountTypeID=USER_ID,
        )
    yield user


@pytest.fixture
def redis():
    redis = redis_connection()

    def delete_keys():
        # Cleanup keys if they exist.
        for key in (
            "package_count",
            "orphan_count",
            "user_count",
            "package_maintainer_count",
            "seven_days_old_added",
            "seven_days_old_updated",
            "year_old_updated",
            "never_updated",
            "package_updates",
        ):
            if redis.get(key) is not None:
                redis.delete(key)

    delete_keys()
    yield redis
    delete_keys()


@pytest.fixture
def package(user: User) -> Generator[Package]:
    now = time.utcnow()
    with db.begin():
        pkgbase = db.create(
            PackageBase,
            Name="test-pkg",
            Maintainer=user,
            Packager=user,
            SubmittedTS=now,
            ModifiedTS=now,
        )
        pkg = db.create(Package, PackageBase=pkgbase, Name=pkgbase.Name)
    yield pkg


@pytest.fixture
def packages(user):
    """Yield a list of num_packages Package objects maintained by user."""
    num_packages = 50  # Tunable

    # For i..num_packages, create a package named pkg_{i}.
    pkgs = []
    now = time.utcnow()
    with db.begin():
        for i in range(num_packages):
            pkgbase = db.create(
                PackageBase,
                Name=f"pkg_{i}",
                Maintainer=user,
                Packager=user,
                SubmittedTS=now,
                ModifiedTS=now,
            )
            pkg = db.create(Package, PackageBase=pkgbase, Name=pkgbase.Name)
            pkgs.append(pkg)
            now += 1

    yield pkgs


def test_homepage():
    with client as request:
        response = request.get("/")
    assert response.status_code == int(HTTPStatus.OK)


@patch("aurweb.util.get_ssh_fingerprints")
def test_homepage_ssh_fingerprints(get_ssh_fingerprints_mock, user):
    fingerprints = {"Ed25519": "SHA256:RFzBCUItH9LZS0cKB5UE6ceAYhBD5C8GeOBip8Z11+4"}
    get_ssh_fingerprints_mock.return_value = fingerprints

    # without authentication (Home)
    with client as request:
        response = request.get("/")

    # with authentication (Dashboard)
    with client as auth_request:
        auth_request.cookies = {"AURSID": user.login(Request(), "testPassword")}
        auth_response = auth_request.get("/")

    for resp in [response, auth_response]:
        for key, value in fingerprints.items():
            assert key in resp.content.decode()
            assert value in resp.content.decode()
        assert (
            "The following SSH fingerprints are used for the AUR"
            in resp.content.decode()
        )


@patch("aurweb.util.get_ssh_fingerprints")
def test_homepage_no_ssh_fingerprints(get_ssh_fingerprints_mock, user):
    get_ssh_fingerprints_mock.return_value = {}

    # without authentication (Home)
    with client as request:
        response = request.get("/")

    # with authentication (Dashboard)
    with client as auth_request:
        auth_request.cookies = {"AURSID": user.login(Request(), "testPassword")}
        auth_response = auth_request.get("/")

    for resp in [response, auth_response]:
        assert (
            "The following SSH fingerprints are used for the AUR"
            not in resp.content.decode()
        )


def test_homepage_stats(redis, packages):
    with client as request:
        response = request.get("/")
    assert response.status_code == int(HTTPStatus.OK)

    root = parse_root(response.text)

    expectations = [
        ("Packages", r"\d+"),
        ("Orphan Packages", r"\d+"),
        ("Packages added in the past 7 days", r"\d+"),
        ("Packages updated in the past 7 days", r"\d+"),
        ("Packages updated in the past year", r"\d+"),
        ("Packages never updated", r"\d+"),
        ("Registered Users", r"\d+"),
        ("Package Maintainers", r"\d+"),
    ]

    stats = root.xpath('//div[@id="pkg-stats"]//tr')
    for i, expected in enumerate(expectations):
        expected_key, expected_regex = expected
        key, value = stats[i].xpath("./td")
        assert key.text.strip() == expected_key
        assert re.match(expected_regex, value.text.strip())


def test_homepage_updates(redis, packages):
    with client as request:
        response = request.get("/")
        assert response.status_code == int(HTTPStatus.OK)
        # Run the request a second time to exercise the Redis path.
        response = request.get("/")
    assert response.status_code == int(HTTPStatus.OK)

    root = parse_root(response.text)

    # We expect to see the latest 15 packages, which happens to be
    # pkg_49 .. pkg_34. So, create a list of expectations using a range
    # starting at 49, stepping down to 49 - 15, -1 step at a time.
    expectations = [f"pkg_{i}" for i in range(50 - 1, 50 - 1 - 15, -1)]
    updates = root.xpath('//div[@id="pkg-updates"]/table/tbody/tr')
    for i, expected in enumerate(expectations):
        pkgname = updates[i].xpath("./td/a").pop(0)
        assert pkgname.text.strip() == expected


def test_homepage_dashboard(redis, packages, user):
    # Create Comaintainer records for all of the packages.
    with db.begin():
        for pkg in packages:
            db.create(
                PackageComaintainer, PackageBase=pkg.PackageBase, User=user, Priority=1
            )

    cookies = {"AURSID": user.login(Request(), "testPassword")}
    with client as request:
        request.cookies = cookies
        response = request.get("/")
    assert response.status_code == int(HTTPStatus.OK)

    root = parse_root(response.text)

    # Assert some expectations that we end up getting all fifty
    # packages in the "My Packages" table.
    expectations = [f"pkg_{i}" for i in range(50 - 1, 0, -1)]
    my_packages = root.xpath('//table[@id="my-packages"]/tbody/tr')
    for i, expected in enumerate(expectations):
        name, version, votes, pop, voted, notify, desc, maint = my_packages[i].xpath(
            "./td"
        )
        assert name.xpath("./a").pop(0).text.strip() == expected

    # Do the same for the Comaintained Packages table.
    my_packages = root.xpath('//table[@id="comaintained-packages"]/tbody/tr')
    for i, expected in enumerate(expectations):
        name, version, votes, pop, voted, notify, desc, maint = my_packages[i].xpath(
            "./td"
        )
        assert name.xpath("./a").pop(0).text.strip() == expected


def test_homepage_dashboard_requests(redis, packages, user):
    now = time.utcnow()

    pkg = packages[0]
    reqtype = db.query(RequestType, RequestType.ID == DELETION_ID).first()
    with db.begin():
        pkgreq = db.create(
            PackageRequest,
            PackageBase=pkg.PackageBase,
            PackageBaseName=pkg.PackageBase.Name,
            User=user,
            Comments=str(),
            ClosureComment=str(),
            RequestTS=now,
            RequestType=reqtype,
        )

    cookies = {"AURSID": user.login(Request(), "testPassword")}
    with client as request:
        request.cookies = cookies
        response = request.get("/")
    assert response.status_code == int(HTTPStatus.OK)

    root = parse_root(response.text)
    request = root.xpath('//table[@id="pkgreq-results"]/tbody/tr').pop(0)
    pkgname = request.xpath("./td/a").pop(0)
    assert pkgname.text.strip() == pkgreq.PackageBaseName


def test_homepage_dashboard_flagged_packages(redis, packages, user):
    # Set the first Package flagged by setting its OutOfDateTS column.
    pkg = packages[0]
    with db.begin():
        pkg.PackageBase.OutOfDateTS = time.utcnow()

    cookies = {"AURSID": user.login(Request(), "testPassword")}
    with client as request:
        request.cookies = cookies
        response = request.get("/")
    assert response.status_code == int(HTTPStatus.OK)

    # Check to see that the package showed up in the Flagged Packages table.
    root = parse_root(response.text)
    flagged_pkg = root.xpath('//table[@id="flagged-packages"]/tbody/tr').pop(0)
    flagged_name = flagged_pkg.xpath("./td/a").pop(0)
    assert flagged_name.text.strip() == pkg.Name


def test_homepage_dashboard_flagged(user: User, user2: User, package: Package):
    pkgbase = package.PackageBase

    now = time.utcnow()
    with db.begin():
        db.create(PackageComaintainer, User=user2, PackageBase=pkgbase, Priority=1)
        pkgbase.OutOfDateTS = now - 5
        pkgbase.Flagger = user

    # Test that a comaintainer viewing the dashboard shows them their
    # flagged co-maintained packages.
    comaint_cookies = {"AURSID": user2.login(Request(), "testPassword")}
    with client as request:
        request.cookies = comaint_cookies
        resp = request.get("/")
    assert resp.status_code == int(HTTPStatus.OK)

    root = parse_root(resp.text)
    flagged = root.xpath('//table[@id="flagged-packages"]//tr/td/a')[0]
    assert flagged.text.strip() == package.Name

    # Test that a maintainer viewing the dashboard shows them their
    # flagged maintained packages.
    cookies = {"AURSID": user.login(Request(), "testPassword")}
    with client as request:
        request.cookies = cookies
        resp = request.get("/")
    assert resp.status_code == int(HTTPStatus.OK)

    root = parse_root(resp.text)
    flagged = root.xpath('//table[@id="flagged-packages"]//tr/td/a')[0]
    assert flagged.text.strip() == package.Name
