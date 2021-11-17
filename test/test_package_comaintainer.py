import pytest

from sqlalchemy.exc import IntegrityError

from aurweb import db
from aurweb.models.package_base import PackageBase
from aurweb.models.package_comaintainer import PackageComaintainer
from aurweb.models.user import User

user = pkgbase = None


@pytest.fixture(autouse=True)
def setup(db_test):
    global user, pkgbase

    with db.begin():
        user = db.create(User, Username="test", Email="test@example.org",
                         RealName="Test User", Passwd="testPassword")
        pkgbase = db.create(PackageBase, Name="test-package", Maintainer=user)


def test_package_comaintainer_creation():
    with db.begin():
        package_comaintainer = db.create(PackageComaintainer, User=user,
                                         PackageBase=pkgbase, Priority=5)
    assert bool(package_comaintainer)
    assert package_comaintainer.User == user
    assert package_comaintainer.PackageBase == pkgbase
    assert package_comaintainer.Priority == 5


def test_package_comaintainer_null_user_raises_exception():
    with pytest.raises(IntegrityError):
        PackageComaintainer(PackageBase=pkgbase, Priority=1)


def test_package_comaintainer_null_pkgbase_raises_exception():
    with pytest.raises(IntegrityError):
        PackageComaintainer(User=user, Priority=1)


def test_package_comaintainer_null_priority_raises_exception():
    with pytest.raises(IntegrityError):
        PackageComaintainer(User=user, PackageBase=pkgbase)
