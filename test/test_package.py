import pytest
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError

from aurweb import db
from aurweb.models.account_type import USER_ID
from aurweb.models.package import Package
from aurweb.models.package_base import PackageBase
from aurweb.models.user import User


@pytest.fixture(autouse=True)
def setup(db_test):
    return


@pytest.fixture
def user() -> User:
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
def package(user: User) -> Package:
    with db.begin():
        pkgbase = db.create(PackageBase, Name="beautiful-package", Maintainer=user)
        package = db.create(
            Package,
            PackageBase=pkgbase,
            Name=pkgbase.Name,
            Description="Test description.",
            URL="https://test.package",
        )
    yield package


def test_package(package: Package):
    assert package.Name == "beautiful-package"
    assert package.Description == "Test description."
    assert package.Version == str()  # Default version.
    assert package.URL == "https://test.package"

    # Update package Version.
    with db.begin():
        package.Version = "1.2.3"

    # Make sure it got updated in the database.
    record = (
        db.query(Package)
        .filter(and_(Package.ID == package.ID, Package.Version == "1.2.3"))
        .first()
    )
    assert record is not None


def test_package_null_pkgbase_raises():
    with pytest.raises(IntegrityError):
        Package(
            Name="some-package",
            Description="Some description.",
            URL="https://some.package",
        )


def test_package_null_name_raises(package: Package):
    pkgbase = package.PackageBase
    with pytest.raises(IntegrityError):
        Package(
            PackageBase=pkgbase,
            Description="Some description.",
            URL="https://some.package",
        )
