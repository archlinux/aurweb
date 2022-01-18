import pytest

from sqlalchemy.exc import IntegrityError

from aurweb import db
from aurweb.models.account_type import USER_ID
from aurweb.models.package_base import PackageBase
from aurweb.models.package_comaintainer import PackageComaintainer
from aurweb.models.user import User


@pytest.fixture(autouse=True)
def setup(db_test):
    return


@pytest.fixture
def user() -> User:
    with db.begin():
        user = db.create(User, Username="test", Email="test@example.org",
                         RealName="Test User", Passwd="testPassword",
                         AccountTypeID=USER_ID)
    yield user


@pytest.fixture
def pkgbase(user: User) -> PackageBase:
    with db.begin():
        pkgbase = db.create(PackageBase, Name="test-package", Maintainer=user)
    yield pkgbase


def test_package_comaintainer_creation(user: User, pkgbase: PackageBase):
    with db.begin():
        package_comaintainer = db.create(PackageComaintainer, User=user,
                                         PackageBase=pkgbase, Priority=5)
    assert bool(package_comaintainer)
    assert package_comaintainer.User == user
    assert package_comaintainer.PackageBase == pkgbase
    assert package_comaintainer.Priority == 5


def test_package_comaintainer_null_user_raises(pkgbase: PackageBase):
    with pytest.raises(IntegrityError):
        PackageComaintainer(PackageBase=pkgbase, Priority=1)


def test_package_comaintainer_null_pkgbase_raises(user: User):
    with pytest.raises(IntegrityError):
        PackageComaintainer(User=user, Priority=1)


def test_package_comaintainer_null_priority_raises(user: User,
                                                   pkgbase: PackageBase):
    with pytest.raises(IntegrityError):
        PackageComaintainer(User=user, PackageBase=pkgbase)
