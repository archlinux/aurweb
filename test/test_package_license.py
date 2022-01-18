import pytest

from sqlalchemy.exc import IntegrityError

from aurweb import db
from aurweb.models.account_type import USER_ID
from aurweb.models.license import License
from aurweb.models.package import Package
from aurweb.models.package_base import PackageBase
from aurweb.models.package_license import PackageLicense
from aurweb.models.user import User


@pytest.fixture(autouse=True)
def setup(db_test):
    return


@pytest.fixture
def user() -> User:
    with db.begin():
        user = db.create(User, Username="test", Email="test@example.org",
                         RealName="Test User", Passwd="testPassword",
                         AccountTypeID=USER_ID)
    yield user


@pytest.fixture
def license() -> License:
    with db.begin():
        license = db.create(License, Name="Test License")
    yield license


@pytest.fixture
def package(user: User, license: License):
    with db.begin():
        pkgbase = db.create(PackageBase, Name="test-package", Maintainer=user)
        package = db.create(Package, PackageBase=pkgbase, Name=pkgbase.Name)
    yield package


def test_package_license(license: License, package: Package):
    with db.begin():
        package_license = db.create(PackageLicense, Package=package,
                                    License=license)
    assert package_license.License == license
    assert package_license.Package == package


def test_package_license_null_package_raises(license: License):
    with pytest.raises(IntegrityError):
        PackageLicense(License=license)


def test_package_license_null_license_raises(package: Package):
    with pytest.raises(IntegrityError):
        PackageLicense(Package=package)
