import pytest

from sqlalchemy.exc import IntegrityError

from aurweb import db
from aurweb.models.package_base import PackageBase
from aurweb.models.package_notification import PackageNotification
from aurweb.models.user import User

user = pkgbase = None


@pytest.fixture(autouse=True)
def setup(db_test):
    global user, pkgbase

    with db.begin():
        user = db.create(User, Username="test", Email="test@example.org",
                         RealName="Test User", Passwd="testPassword")
        pkgbase = db.create(PackageBase, Name="test-package", Maintainer=user)


def test_package_notification_creation():
    with db.begin():
        package_notification = db.create(
            PackageNotification, User=user, PackageBase=pkgbase)
    assert bool(package_notification)
    assert package_notification.User == user
    assert package_notification.PackageBase == pkgbase


def test_package_notification_null_user_raises_exception():
    with pytest.raises(IntegrityError):
        PackageNotification(PackageBase=pkgbase)


def test_package_notification_null_pkgbase_raises_exception():
    with pytest.raises(IntegrityError):
        PackageNotification(User=user)
