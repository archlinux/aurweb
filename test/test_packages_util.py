from datetime import datetime

import pytest

from fastapi import HTTPException
from fastapi.testclient import TestClient

from aurweb import asgi, db
from aurweb.models.account_type import USER_ID
from aurweb.models.official_provider import OFFICIAL_BASE, OfficialProvider
from aurweb.models.package import Package
from aurweb.models.package_base import PackageBase
from aurweb.models.package_notification import PackageNotification
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


def test_package_link(client: TestClient, maintainer: User, package: Package):
    with db.begin():
        db.create(OfficialProvider,
                  Name=package.Name,
                  Repo="core",
                  Provides=package.Name)
    expected = f"{OFFICIAL_BASE}/packages/?q={package.Name}"
    assert util.package_link(package) == expected


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
