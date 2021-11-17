import pytest

from sqlalchemy.exc import IntegrityError

import aurweb.config

from aurweb import db
from aurweb.models.account_type import AccountType
from aurweb.models.package_base import PackageBase
from aurweb.models.user import User

user = None


@pytest.fixture(autouse=True)
def setup(db_test):
    global user

    account_type = db.query(AccountType,
                            AccountType.AccountType == "User").first()
    with db.begin():
        user = db.create(User, Username="test", Email="test@example.org",
                         RealName="Test User", Passwd="testPassword",
                         AccountType=account_type)


def test_package_base():
    with db.begin():
        pkgbase = db.create(PackageBase,
                            Name="beautiful-package",
                            Maintainer=user)
    assert pkgbase in user.maintained_bases

    assert not pkgbase.OutOfDateTS
    assert pkgbase.SubmittedTS > 0
    assert pkgbase.ModifiedTS > 0

    # Set Popularity to a string, then get it by attribute to
    # exercise the string -> float conversion path.
    with db.begin():
        pkgbase.Popularity = "0.0"
    assert pkgbase.Popularity == 0.0


def test_package_base_ci():
    """ Test case insensitivity of the database table. """
    if aurweb.config.get("database", "backend") == "sqlite":
        return None  # SQLite doesn't seem handle this.

    with db.begin():
        pkgbase = db.create(PackageBase,
                            Name="beautiful-package",
                            Maintainer=user)
    assert bool(pkgbase.ID)

    with pytest.raises(IntegrityError):
        with db.begin():
            db.create(PackageBase,
                      Name="Beautiful-Package",
                      Maintainer=user)
    db.rollback()


def test_package_base_relationships():
    with db.begin():
        pkgbase = db.create(PackageBase,
                            Name="beautiful-package",
                            Flagger=user,
                            Maintainer=user,
                            Submitter=user,
                            Packager=user)
    assert pkgbase in user.flagged_bases
    assert pkgbase in user.maintained_bases
    assert pkgbase in user.submitted_bases
    assert pkgbase in user.package_bases


def test_package_base_null_name_raises_exception():
    with pytest.raises(IntegrityError):
        with db.begin():
            db.create(PackageBase)
    db.rollback()
