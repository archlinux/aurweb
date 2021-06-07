import pytest

from sqlalchemy.exc import IntegrityError

from aurweb.db import create, query
from aurweb.models.account_type import AccountType
from aurweb.models.license import License
from aurweb.models.package import Package
from aurweb.models.package_base import PackageBase
from aurweb.models.package_license import PackageLicense
from aurweb.models.user import User
from aurweb.testing import setup_test_db

user = license = pkgbase = package = None


@pytest.fixture(autouse=True)
def setup():
    global user, license, pkgbase, package

    setup_test_db("Users", "PackageBases", "Packages",
                  "Licenses", "PackageLicenses")

    account_type = query(AccountType,
                         AccountType.AccountType == "User").first()
    user = create(User, Username="test", Email="test@example.org",
                  RealName="Test User", Passwd="testPassword",
                  AccountType=account_type)

    license = create(License, Name="Test License")
    pkgbase = create(PackageBase, Name="test-package", Maintainer=user)
    package = create(Package, PackageBase=pkgbase, Name=pkgbase.Name)


def test_package_license():
    package_license = create(PackageLicense, Package=package, License=license)
    assert package_license.License == license
    assert package_license.Package == package


def test_package_license_null_package_raises_exception():
    from aurweb.db import session
    with pytest.raises(IntegrityError):
        create(PackageLicense, License=license)
    session.rollback()


def test_package_license_null_license_raises_exception():
    from aurweb.db import session
    with pytest.raises(IntegrityError):
        create(PackageLicense, Package=package)
    session.rollback()
