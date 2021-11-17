import pytest

from sqlalchemy.exc import IntegrityError

from aurweb import db
from aurweb.models.account_type import USER_ID
from aurweb.models.dependency_type import CHECKDEPENDS_ID, DEPENDS_ID, MAKEDEPENDS_ID, OPTDEPENDS_ID
from aurweb.models.package import Package
from aurweb.models.package_base import PackageBase
from aurweb.models.package_dependency import PackageDependency
from aurweb.models.user import User

user = pkgbase = package = None


@pytest.fixture(autouse=True)
def setup(db_test):
    global user, pkgbase, package

    with db.begin():
        user = db.create(User, Username="test", Email="test@example.org",
                         RealName="Test User", Passwd="testPassword",
                         AccountTypeID=USER_ID)
        pkgbase = db.create(PackageBase,
                            Name="test-package",
                            Maintainer=user)
        package = db.create(Package,
                            PackageBase=pkgbase,
                            Name=pkgbase.Name,
                            Description="Test description.",
                            URL="https://test.package")


def test_package_dependencies():
    with db.begin():
        pkgdep = db.create(PackageDependency, Package=package,
                           DepTypeID=DEPENDS_ID, DepName="test-dep")
    assert pkgdep.DepName == "test-dep"
    assert pkgdep.Package == package
    assert pkgdep in package.package_dependencies

    with db.begin():
        pkgdep.DepTypeID = MAKEDEPENDS_ID

    with db.begin():
        pkgdep.DepTypeID = CHECKDEPENDS_ID

    with db.begin():
        pkgdep.DepTypeID = OPTDEPENDS_ID

    assert not pkgdep.is_package()

    with db.begin():
        base = db.create(PackageBase, Name=pkgdep.DepName, Maintainer=user)
        db.create(Package, PackageBase=base, Name=pkgdep.DepName)

    assert pkgdep.is_package()


def test_package_dependencies_null_package_raises_exception():
    with pytest.raises(IntegrityError):
        PackageDependency(DepTypeID=DEPENDS_ID, DepName="test-dep")


def test_package_dependencies_null_dependency_type_raises_exception():
    with pytest.raises(IntegrityError):
        PackageDependency(Package=package, DepName="test-dep")


def test_package_dependencies_null_depname_raises_exception():
    with pytest.raises(IntegrityError):
        PackageDependency(DepTypeID=DEPENDS_ID, Package=package)
