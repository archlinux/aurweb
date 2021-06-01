import pytest

from sqlalchemy.exc import IntegrityError

from aurweb.db import create, query
from aurweb.models.account_type import AccountType
from aurweb.models.package_base import PackageBase
from aurweb.models.package_keyword import PackageKeyword
from aurweb.testing import setup_test_db
from aurweb.testing.models import make_user

user, pkgbase = None, None


@pytest.fixture(autouse=True)
def setup():
    global user, pkgbase

    setup_test_db("Users", "PackageBases", "PackageKeywords")

    account_type = query(AccountType,
                         AccountType.AccountType == "User").first()
    user = make_user(Username="test", Email="test@example.org",
                     RealName="Test User", Passwd="testPassword",
                     AccountType=account_type)
    pkgbase = create(PackageBase,
                     Name="beautiful-package",
                     Maintainer=user)

    yield pkgbase


def test_package_keyword():
    pkg_keyword = create(PackageKeyword,
                         PackageBase=pkgbase,
                         Keyword="test")
    assert pkg_keyword in pkgbase.keywords
    assert pkgbase == pkg_keyword.PackageBase


def test_package_keyword_null_pkgbase_raises_exception():
    from aurweb.db import session

    with pytest.raises(IntegrityError):
        create(PackageKeyword,
               Keyword="test")
    session.rollback()
