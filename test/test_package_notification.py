import pytest

from sqlalchemy.exc import IntegrityError

from aurweb.db import create, rollback
from aurweb.models.package_base import PackageBase
from aurweb.models.package_notification import PackageNotification
from aurweb.models.user import User
from aurweb.testing import setup_test_db

user = pkgbase = None


@pytest.fixture(autouse=True)
def setup():
    global user, pkgbase

    setup_test_db("Users", "PackageBases", "PackageNotifications")

    user = create(User, Username="test", Email="test@example.org",
                  RealName="Test User", Passwd="testPassword")
    pkgbase = create(PackageBase, Name="test-package", Maintainer=user)


def test_package_notification_creation():
    package_notification = create(PackageNotification, User=user,
                                  PackageBase=pkgbase)
    assert bool(package_notification)
    assert package_notification.User == user
    assert package_notification.PackageBase == pkgbase


def test_package_notification_null_user_raises_exception():
    with pytest.raises(IntegrityError):
        create(PackageNotification, PackageBase=pkgbase)
    rollback()


def test_package_notification_null_pkgbase_raises_exception():
    with pytest.raises(IntegrityError):
        create(PackageNotification, User=user)
    rollback()
