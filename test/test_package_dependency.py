import pytest

from sqlalchemy.exc import IntegrityError

from aurweb import db
from aurweb.db import create, query
from aurweb.models.account_type import AccountType
from aurweb.models.dependency_type import DependencyType
from aurweb.models.package import Package
from aurweb.models.package_base import PackageBase
from aurweb.models.package_dependency import PackageDependency
from aurweb.models.user import User
from aurweb.testing import setup_test_db

user = pkgbase = package = None


@pytest.fixture(autouse=True)
def setup():
    global user, pkgbase, package

    setup_test_db("Users", "PackageBases", "Packages", "PackageDepends")

    account_type = query(AccountType,
                         AccountType.AccountType == "User").first()

    with db.begin():
        user = create(User, Username="test", Email="test@example.org",
                      RealName="Test User", Passwd="testPassword",
                      AccountType=account_type)
        pkgbase = create(PackageBase,
                         Name="test-package",
                         Maintainer=user)
        package = create(Package,
                         PackageBase=pkgbase,
                         Name=pkgbase.Name,
                         Description="Test description.",
                         URL="https://test.package")


def test_package_dependencies():
    depends = query(DependencyType, DependencyType.Name == "depends").first()

    with db.begin():
        pkgdep = create(PackageDependency, Package=package,
                        DependencyType=depends,
                        DepName="test-dep")
    assert pkgdep.DepName == "test-dep"
    assert pkgdep.Package == package
    assert pkgdep.DependencyType == depends
    assert pkgdep in depends.package_dependencies
    assert pkgdep in package.package_dependencies

    makedepends = query(DependencyType,
                        DependencyType.Name == "makedepends").first()
    with db.begin():
        pkgdep.DependencyType = makedepends
    assert pkgdep.DepName == "test-dep"
    assert pkgdep.Package == package
    assert pkgdep.DependencyType == makedepends
    assert pkgdep in makedepends.package_dependencies
    assert pkgdep in package.package_dependencies

    checkdepends = query(DependencyType,
                         DependencyType.Name == "checkdepends").first()
    with db.begin():
        pkgdep.DependencyType = checkdepends
    assert pkgdep.DepName == "test-dep"
    assert pkgdep.Package == package
    assert pkgdep.DependencyType == checkdepends
    assert pkgdep in checkdepends.package_dependencies
    assert pkgdep in package.package_dependencies

    optdepends = query(DependencyType,
                       DependencyType.Name == "optdepends").first()
    with db.begin():
        pkgdep.DependencyType = optdepends
    assert pkgdep.DepName == "test-dep"
    assert pkgdep.Package == package
    assert pkgdep.DependencyType == optdepends
    assert pkgdep in optdepends.package_dependencies
    assert pkgdep in package.package_dependencies

    assert not pkgdep.is_package()

    with db.begin():
        base = create(PackageBase, Name=pkgdep.DepName, Maintainer=user)
        create(Package, PackageBase=base, Name=pkgdep.DepName)

    assert pkgdep.is_package()


def test_package_dependencies_null_package_raises_exception():
    depends = query(DependencyType, DependencyType.Name == "depends").first()
    with pytest.raises(IntegrityError):
        with db.begin():
            create(PackageDependency,
                   DependencyType=depends,
                   DepName="test-dep")
    db.rollback()


def test_package_dependencies_null_dependency_type_raises_exception():
    with pytest.raises(IntegrityError):
        with db.begin():
            create(PackageDependency,
                   Package=package,
                   DepName="test-dep")
    db.rollback()


def test_package_dependencies_null_depname_raises_exception():
    depends = query(DependencyType, DependencyType.Name == "depends").first()
    with pytest.raises(IntegrityError):
        with db.begin():
            create(PackageDependency,
                   Package=package,
                   DependencyType=depends)
    db.rollback()
