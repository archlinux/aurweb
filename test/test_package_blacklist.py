import pytest

from sqlalchemy.exc import IntegrityError

from aurweb.db import create, rollback
from aurweb.models.package_base import PackageBase
from aurweb.models.package_blacklist import PackageBlacklist
from aurweb.models.user import User
from aurweb.testing import setup_test_db

user = pkgbase = None


@pytest.fixture(autouse=True)
def setup():
    global user, pkgbase

    setup_test_db("PackageBlacklist", "PackageBases", "Users")

    user = create(User, Username="test", Email="test@example.org",
                  RealName="Test User", Passwd="testPassword")
    pkgbase = create(PackageBase, Name="test-package", Maintainer=user)


def test_package_blacklist_creation():
    package_blacklist = create(PackageBlacklist, Name="evil-package")
    assert bool(package_blacklist.ID)
    assert package_blacklist.Name == "evil-package"


def test_package_blacklist_null_name_raises_exception():
    with pytest.raises(IntegrityError):
        create(PackageBlacklist)
    rollback()
