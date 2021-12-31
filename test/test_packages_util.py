from datetime import datetime

import pytest

from fastapi import HTTPException
from fastapi.testclient import TestClient

from aurweb import asgi, config, db
from aurweb.models.account_type import USER_ID
from aurweb.models.official_provider import OFFICIAL_BASE, OfficialProvider
from aurweb.models.package import Package
from aurweb.models.package_base import PackageBase
from aurweb.models.package_notification import PackageNotification
from aurweb.models.package_source import PackageSource
from aurweb.models.package_vote import PackageVote
from aurweb.models.user import User
from aurweb.packages import util
from aurweb.redis import kill_redis


@pytest.fixture(autouse=True)
def setup(db_test):
    return


@pytest.fixture
def maintainer() -> User:
    with db.begin():
        maintainer = db.create(User, Username="test_maintainer",
                               Email="test_maintainer@examepl.org",
                               Passwd="testPassword",
                               AccountTypeID=USER_ID)
    yield maintainer


@pytest.fixture
def package(maintainer: User) -> Package:
    with db.begin():
        pkgbase = db.create(PackageBase, Name="test-pkg",
                            Packager=maintainer, Maintainer=maintainer)
        package = db.create(Package, Name=pkgbase.Name, PackageBase=pkgbase)
    yield package


@pytest.fixture
def client() -> TestClient:
    yield TestClient(app=asgi.app)


def test_package_link(client: TestClient, package: Package):
    expected = f"/packages/{package.Name}"
    assert util.package_link(package) == expected


def test_official_package_link(client: TestClient, package: Package):
    with db.begin():
        provider = db.create(OfficialProvider,
                             Name=package.Name,
                             Repo="core",
                             Provides=package.Name)
    expected = f"{OFFICIAL_BASE}/packages/?q={package.Name}"
    assert util.package_link(provider) == expected


def test_updated_packages(maintainer: User, package: Package):
    expected = {
        "Name": package.Name,
        "Version": package.Version,
        "PackageBase": {
            "ModifiedTS": package.PackageBase.ModifiedTS
        }
    }

    kill_redis()  # Kill it here to ensure we're on a fake instance.
    assert util.updated_packages(1, 0) == [expected]
    assert util.updated_packages(1, 600) == [expected]
    kill_redis()  # Kill it again, in case other tests use a real instance.


def test_query_voted(maintainer: User, package: Package):
    now = int(datetime.utcnow().timestamp())
    with db.begin():
        db.create(PackageVote, User=maintainer, VoteTS=now,
                  PackageBase=package.PackageBase)

    query = db.query(Package).filter(Package.ID == package.ID).all()
    query_voted = util.query_voted(query, maintainer)
    assert query_voted[package.PackageBase.ID]


def test_query_notified(maintainer: User, package: Package):
    with db.begin():
        db.create(PackageNotification, User=maintainer,
                  PackageBase=package.PackageBase)

    query = db.query(Package).filter(Package.ID == package.ID).all()
    query_notified = util.query_notified(query, maintainer)
    assert query_notified[package.PackageBase.ID]


def test_pkgreq_by_id_not_found():
    with pytest.raises(HTTPException):
        util.get_pkgreq_by_id(0)


def test_source_uri_file(package: Package):
    FILE = "test_file"

    with db.begin():
        pkgsrc = db.create(PackageSource, Source=FILE,
                           Package=package, SourceArch="x86_64")
    source_file_uri = config.get("options", "source_file_uri")
    file, uri = util.source_uri(pkgsrc)
    expected = source_file_uri % (pkgsrc.Source, package.PackageBase.Name)
    assert (file, uri) == (FILE, expected)


def test_source_uri_named_uri(package: Package):
    FILE = "test"
    URL = "https://test.xyz"

    with db.begin():
        pkgsrc = db.create(PackageSource, Source=f"{FILE}::{URL}",
                           Package=package, SourceArch="x86_64")
    file, uri = util.source_uri(pkgsrc)
    assert (file, uri) == (FILE, URL)


def test_source_uri_unnamed_uri(package: Package):
    URL = "https://test.xyz"

    with db.begin():
        pkgsrc = db.create(PackageSource, Source=f"{URL}",
                           Package=package, SourceArch="x86_64")
    file, uri = util.source_uri(pkgsrc)
    assert (file, uri) == (URL, URL)
