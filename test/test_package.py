import pytest

from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError

from aurweb.db import create, query
from aurweb.models.account_type import AccountType
from aurweb.models.package import Package
from aurweb.models.package_base import PackageBase
from aurweb.models.user import User
from aurweb.testing import setup_test_db

user = pkgbase = package = None


@pytest.fixture(autouse=True)
def setup():
    global user, pkgbase, package

    setup_test_db("Users", "PackageBases", "Packages")

    account_type = query(AccountType,
                         AccountType.AccountType == "User").first()
    user = create(User, Username="test", Email="test@example.org",
                  RealName="Test User", Passwd="testPassword",
                  AccountType=account_type)

    pkgbase = create(PackageBase,
                     Name="beautiful-package",
                     Maintainer=user)
    package = create(Package,
                     PackageBase=pkgbase,
                     Name=pkgbase.Name,
                     Description="Test description.",
                     URL="https://test.package")

    yield package


def test_package():
    from aurweb.db import session

    assert pkgbase == package.PackageBase
    assert package.Name == "beautiful-package"
    assert package.Description == "Test description."
    assert package.Version == str()  # Default version.
    assert package.URL == "https://test.package"

    # Update package Version.
    package.Version = "1.2.3"
    session.commit()

    # Make sure it got updated in the database.
    record = query(Package,
                   and_(Package.ID == package.ID,
                        Package.Version == "1.2.3")).first()
    assert record is not None


def test_package_null_pkgbase_raises_exception():
    from aurweb.db import session

    with pytest.raises(IntegrityError):
        create(Package,
               Name="some-package",
               Description="Some description.",
               URL="https://some.package")
    session.rollback()


def test_package_null_name_raises_exception():
    from aurweb.db import session

    with pytest.raises(IntegrityError):
        create(Package,
               PackageBase=pkgbase,
               Description="Some description.",
               URL="https://some.package")
    session.rollback()
