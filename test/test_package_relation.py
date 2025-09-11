from typing import Generator

import pytest
from sqlalchemy.exc import IntegrityError

from aurweb import db
from aurweb.models.account_type import USER_ID
from aurweb.models.package import Package
from aurweb.models.package_base import PackageBase
from aurweb.models.package_relation import PackageRelation
from aurweb.models.relation_type import CONFLICTS_ID, PROVIDES_ID, REPLACES_ID
from aurweb.models.user import User


@pytest.fixture(autouse=True)
def setup(db_test):
    return


@pytest.fixture
def user() -> Generator[User]:
    with db.begin():
        user = db.create(
            User,
            Username="test",
            Email="test@example.org",
            RealName="Test User",
            Passwd="testPassword",
            AccountTypeID=USER_ID,
        )
    yield user


@pytest.fixture
def package(user: User) -> Generator[Package]:
    with db.begin():
        pkgbase = db.create(PackageBase, Name="test-package", Maintainer=user)
        package = db.create(
            Package,
            PackageBase=pkgbase,
            Name=pkgbase.Name,
            Description="Test description.",
            URL="https://test.package",
        )
    yield package


def test_package_relation(package: Package):
    with db.begin():
        pkgrel = db.create(
            PackageRelation,
            Package=package,
            RelTypeID=CONFLICTS_ID,
            RelName="test-relation",
        )

    assert pkgrel.RelName == "test-relation"
    assert pkgrel.Package == package
    assert pkgrel in package.package_relations

    with db.begin():
        pkgrel.RelTypeID = PROVIDES_ID

    with db.begin():
        pkgrel.RelTypeID = REPLACES_ID


def test_package_relation_null_package_raises():
    with pytest.raises(IntegrityError):
        PackageRelation(RelTypeID=CONFLICTS_ID, RelName="test-relation")


def test_package_relation_null_relation_type_raises(package: Package):
    with pytest.raises(IntegrityError):
        PackageRelation(Package=package, RelName="test-relation")


def test_package_relation_null_relname_raises(package: Package):
    with pytest.raises(IntegrityError):
        PackageRelation(Package=package, RelTypeID=CONFLICTS_ID)
