import pytest

from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError

from aurweb import db
from aurweb.models.account_type import AccountType
from aurweb.models.package import Package
from aurweb.models.package_base import PackageBase
from aurweb.models.user import User
from aurweb.testing import setup_test_db

user = pkgbase = package = None


@pytest.fixture(autouse=True)
def setup():
    global user, pkgbase, package

    setup_test_db("Packages", "PackageBases", "Users")

    account_type = db.query(AccountType,
                            AccountType.AccountType == "User").first()

    with db.begin():
        user = db.create(User, Username="test", Email="test@example.org",
                         RealName="Test User", Passwd="testPassword",
                         AccountType=account_type)

        pkgbase = db.create(PackageBase,
                            Name="beautiful-package",
                            Maintainer=user)
        package = db.create(Package,
                            PackageBase=pkgbase,
                            Name=pkgbase.Name,
                            Description="Test description.",
                            URL="https://test.package")


def test_package():
    assert pkgbase == package.PackageBase
    assert package.Name == "beautiful-package"
    assert package.Description == "Test description."
    assert package.Version == str()  # Default version.
    assert package.URL == "https://test.package"

    # Update package Version.
    with db.begin():
        package.Version = "1.2.3"

    # Make sure it got updated in the database.
    record = db.query(Package,
                      and_(Package.ID == package.ID,
                           Package.Version == "1.2.3")).first()
    assert record is not None


def test_package_null_pkgbase_raises_exception():
    with pytest.raises(IntegrityError):
        with db.begin():
            db.create(Package,
                      Name="some-package",
                      Description="Some description.",
                      URL="https://some.package")
    db.rollback()


def test_package_null_name_raises_exception():
    with pytest.raises(IntegrityError):
        with db.begin():
            db.create(Package,
                      PackageBase=pkgbase,
                      Description="Some description.",
                      URL="https://some.package")
    db.rollback()
