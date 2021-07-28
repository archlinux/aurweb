import pytest

from fastapi.testclient import TestClient

from aurweb import asgi, db
from aurweb.models.account_type import USER_ID, AccountType
from aurweb.models.official_provider import OFFICIAL_BASE, OfficialProvider
from aurweb.models.package import Package
from aurweb.models.package_base import PackageBase
from aurweb.models.user import User
from aurweb.packages import util
from aurweb.redis import kill_redis
from aurweb.testing import setup_test_db


@pytest.fixture(autouse=True)
def setup():
    setup_test_db(
        User.__tablename__,
        Package.__tablename__,
        PackageBase.__tablename__,
        OfficialProvider.__tablename__
    )


@pytest.fixture
def maintainer() -> User:
    account_type = db.query(AccountType, AccountType.ID == USER_ID).first()
    yield db.create(User, Username="test_maintainer",
                    Email="test_maintainer@examepl.org",
                    Passwd="testPassword",
                    AccountType=account_type)


@pytest.fixture
def package(maintainer: User) -> Package:
    pkgbase = db.create(PackageBase, Name="test-pkg",
                        Packager=maintainer, Maintainer=maintainer)
    yield db.create(Package, Name=pkgbase.Name, PackageBase=pkgbase)


@pytest.fixture
def client() -> TestClient:
    yield TestClient(app=asgi.app)


def test_package_link(client: TestClient, maintainer: User, package: Package):
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
