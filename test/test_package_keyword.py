import pytest

from sqlalchemy.exc import IntegrityError

from aurweb import db
from aurweb.models.account_type import USER_ID
from aurweb.models.package_base import PackageBase
from aurweb.models.package_keyword import PackageKeyword
from aurweb.models.user import User

user = pkgbase = None


@pytest.fixture(autouse=True)
def setup(db_test):
    global user, pkgbase

    with db.begin():
        user = db.create(User, Username="test", Email="test@example.org",
                         RealName="Test User", Passwd="testPassword",
                         AccountTypeID=USER_ID)
        pkgbase = db.create(PackageBase,
                            Name="beautiful-package",
                            Maintainer=user)


def test_package_keyword():
    with db.begin():
        pkg_keyword = db.create(PackageKeyword,
                                PackageBase=pkgbase,
                                Keyword="test")
    assert pkg_keyword in pkgbase.keywords
    assert pkgbase == pkg_keyword.PackageBase


def test_package_keyword_null_pkgbase_raises_exception():
    with pytest.raises(IntegrityError):
        PackageKeyword(Keyword="test")
