import pytest

from sqlalchemy.exc import IntegrityError

from aurweb.db import begin, create, query, rollback
from aurweb.models.account_type import AccountType
from aurweb.models.package import Package
from aurweb.models.package_base import PackageBase
from aurweb.models.package_source import PackageSource
from aurweb.models.user import User
from aurweb.testing import setup_test_db

user = pkgbase = package = None


@pytest.fixture(autouse=True)
def setup():
    global user, pkgbase, package

    setup_test_db("PackageSources", "Packages", "PackageBases", "Users")

    account_type = query(AccountType,
                         AccountType.AccountType == "User").first()
    with begin():
        user = create(User, Username="test", Email="test@example.org",
                      RealName="Test User", Passwd="testPassword",
                      AccountType=account_type)
        pkgbase = create(PackageBase,
                         Name="test-package",
                         Maintainer=user)
        package = create(Package, PackageBase=pkgbase, Name="test-package")


def test_package_source():
    with begin():
        pkgsource = create(PackageSource, Package=package)
    assert pkgsource.Package == package
    # By default, PackageSources.Source assigns the string '/dev/null'.
    assert pkgsource.Source == "/dev/null"
    assert pkgsource.SourceArch is None


def test_package_source_null_package_raises_exception():
    with pytest.raises(IntegrityError):
        with begin():
            create(PackageSource)
    rollback()
