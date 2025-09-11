from typing import Generator

import pytest
from sqlalchemy.exc import IntegrityError

from aurweb import db
from aurweb.models.account_type import USER_ID
from aurweb.models.package import Package
from aurweb.models.package_base import PackageBase
from aurweb.models.package_source import PackageSource
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
        package = db.create(Package, PackageBase=pkgbase, Name="test-package")
    yield package


def test_package_source(package: Package):
    with db.begin():
        pkgsource = db.create(PackageSource, Package=package)
    assert pkgsource.Package == package
    # By default, PackageSources.Source assigns the string '/dev/null'.
    assert pkgsource.Source == "/dev/null"
    assert pkgsource.SourceArch is None


def test_package_source_null_package_raises():
    with pytest.raises(IntegrityError):
        PackageSource()
