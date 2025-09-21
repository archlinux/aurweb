from typing import Generator

import pytest
from sqlalchemy.exc import IntegrityError

from aurweb import db
from aurweb.models.account_type import USER_ID
from aurweb.models.package_base import PackageBase
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
def pkgbase(user: User) -> Generator[PackageBase]:
    with db.begin():
        pkgbase = db.create(PackageBase, Name="beautiful-package", Maintainer=user)
    yield pkgbase


def test_package_base(user: User, pkgbase: PackageBase) -> None:
    assert pkgbase in user.maintained_bases
    assert not pkgbase.OutOfDateTS
    assert pkgbase.SubmittedTS > 0
    assert pkgbase.ModifiedTS > 0

    # Set Popularity to a string, then get it by attribute to
    # exercise the string -> float conversion path.
    with db.begin():
        pkgbase.Popularity = "0.0"
    assert pkgbase.Popularity == 0.0


def test_package_base_ci(user: User, pkgbase: PackageBase) -> None:
    """Test case insensitivity of the database table."""
    with pytest.raises(IntegrityError):
        with db.begin():
            db.create(PackageBase, Name=pkgbase.Name.upper(), Maintainer=user)
    db.rollback()


def test_package_base_relationships(user: User, pkgbase: PackageBase) -> None:
    with db.begin():
        pkgbase.Flagger = user
        pkgbase.Submitter = user
        pkgbase.Packager = user
    assert pkgbase in user.flagged_bases
    assert pkgbase in user.maintained_bases
    assert pkgbase in user.submitted_bases
    assert pkgbase in user.package_bases


def test_package_base_null_name_raises_exception() -> None:
    with pytest.raises(IntegrityError):
        PackageBase()
