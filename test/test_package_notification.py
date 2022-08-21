import pytest
from sqlalchemy.exc import IntegrityError

from aurweb import db
from aurweb.models.package_base import PackageBase
from aurweb.models.package_notification import PackageNotification
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
        )
    yield user


@pytest.fixture
def pkgbase(user: User) -> PackageBase:
    with db.begin():
        pkgbase = db.create(PackageBase, Name="test-package", Maintainer=user)
    yield pkgbase


def test_package_notification_creation(user: User, pkgbase: PackageBase):
    with db.begin():
        package_notification = db.create(
            PackageNotification, User=user, PackageBase=pkgbase
        )
    assert bool(package_notification)
    assert package_notification.User == user
    assert package_notification.PackageBase == pkgbase


def test_package_notification_null_user_raises(pkgbase: PackageBase):
    with pytest.raises(IntegrityError):
        PackageNotification(PackageBase=pkgbase)


def test_package_notification_null_pkgbase_raises(user: User):
    with pytest.raises(IntegrityError):
        PackageNotification(User=user)
