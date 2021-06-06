import pytest

from sqlalchemy.exc import IntegrityError

import aurweb.config

from aurweb.db import create, query
from aurweb.models.account_type import AccountType
from aurweb.models.package_base import PackageBase
from aurweb.models.user import User
from aurweb.testing import setup_test_db

user = None


@pytest.fixture(autouse=True)
def setup():
    global user

    setup_test_db("Users", "PackageBases")

    account_type = query(AccountType,
                         AccountType.AccountType == "User").first()
    user = create(User, Username="test", Email="test@example.org",
                  RealName="Test User", Passwd="testPassword",
                  AccountType=account_type)


def test_package_base():
    pkgbase = create(PackageBase,
                     Name="beautiful-package",
                     Maintainer=user)
    assert pkgbase in user.maintained_bases

    assert not pkgbase.OutOfDateTS
    assert pkgbase.SubmittedTS > 0
    assert pkgbase.ModifiedTS > 0


def test_package_base_ci():
    """ Test case insensitivity of the database table. """
    if aurweb.config.get("database", "backend") == "sqlite":
        return None  # SQLite doesn't seem handle this.

    from aurweb.db import session

    pkgbase = create(PackageBase,
                     Name="beautiful-package",
                     Maintainer=user)
    assert bool(pkgbase.ID)

    with pytest.raises(IntegrityError):
        create(PackageBase,
               Name="Beautiful-Package",
               Maintainer=user)
    session.rollback()


def test_package_base_relationships():
    pkgbase = create(PackageBase,
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
    from aurweb.db import session

    with pytest.raises(IntegrityError):
        create(PackageBase)
    session.rollback()
