import pytest

from sqlalchemy.exc import IntegrityError

from aurweb.db import create, rollback
from aurweb.models.package_base import PackageBase
from aurweb.models.package_comaintainer import PackageComaintainer
from aurweb.models.user import User
from aurweb.testing import setup_test_db

user = pkgbase = None


@pytest.fixture(autouse=True)
def setup():
    global user, pkgbase

    setup_test_db("Users", "PackageBases", "PackageComaintainers")

    user = create(User, Username="test", Email="test@example.org",
                  RealName="Test User", Passwd="testPassword")
    pkgbase = create(PackageBase, Name="test-package", Maintainer=user)


def test_package_comaintainer_creation():
    package_comaintainer = create(PackageComaintainer, User=user,
                                  PackageBase=pkgbase, Priority=5)
    assert bool(package_comaintainer)
    assert package_comaintainer.User == user
    assert package_comaintainer.PackageBase == pkgbase
    assert package_comaintainer.Priority == 5


def test_package_comaintainer_null_user_raises_exception():
    with pytest.raises(IntegrityError):
        create(PackageComaintainer, PackageBase=pkgbase, Priority=1)
    rollback()


def test_package_comaintainer_null_pkgbase_raises_exception():
    with pytest.raises(IntegrityError):
        create(PackageComaintainer, User=user, Priority=1)
    rollback()


def test_package_comaintainer_null_priority_raises_exception():
    with pytest.raises(IntegrityError):
        create(PackageComaintainer, User=user, PackageBase=pkgbase)
    rollback()
