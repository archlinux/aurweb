from typing import Generator

import pytest
from sqlalchemy.exc import IntegrityError

from aurweb import db
from aurweb.models.account_type import USER_ID
from aurweb.models.dependency_type import DEPENDS_ID
from aurweb.models.official_provider import OfficialProvider
from aurweb.models.package import Package
from aurweb.models.package_base import PackageBase
from aurweb.models.package_dependency import PackageDependency
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
            Passwd=str(),
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


def is_aur_package(dep: PackageDependency) -> bool:
    exists = db.query(Package).filter(Package.Name == dep.DepName).exists()
    return db.query(exists).scalar()


def is_official_package(dep: PackageDependency) -> bool:
    exists = (
        db.query(OfficialProvider).filter(OfficialProvider.Name == dep.DepName).exists()
    )
    return db.query(exists).scalar()


def is_package(dep: PackageDependency) -> bool:
    return is_aur_package(dep) or is_official_package(dep)


def test_package_dependencies(user: User, package: Package):
    with db.begin():
        pkgdep = db.create(
            PackageDependency, Package=package, DepTypeID=DEPENDS_ID, DepName="test-dep"
        )

    assert pkgdep.DepName == "test-dep"
    assert pkgdep.Package == package
    assert pkgdep in package.package_dependencies
    assert not is_package(pkgdep)

    with db.begin():
        base = db.create(PackageBase, Name=pkgdep.DepName, Maintainer=user)
        db.create(Package, PackageBase=base, Name=pkgdep.DepName)

    assert is_package(pkgdep)
    assert is_aur_package(pkgdep)

    # Test with OfficialProvider
    with db.begin():
        pkgdep = db.create(
            PackageDependency,
            Package=package,
            DepTypeID=DEPENDS_ID,
            DepName="test-repo-pkg",
        )
        db.create(
            OfficialProvider, Name=pkgdep.DepName, Repo="extra", Provides=pkgdep.DepName
        )

    assert is_package(pkgdep)
    assert is_official_package(pkgdep)
    assert not is_aur_package(pkgdep)


def test_package_dependencies_null_package_raises():
    with pytest.raises(IntegrityError):
        PackageDependency(DepTypeID=DEPENDS_ID, DepName="test-dep")


def test_package_dependencies_null_dependency_type_raises(package: Package):
    with pytest.raises(IntegrityError):
        PackageDependency(Package=package, DepName="test-dep")


def test_package_dependencies_null_depname_raises(package: Package):
    with pytest.raises(IntegrityError):
        PackageDependency(DepTypeID=DEPENDS_ID, Package=package)
