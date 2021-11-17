import pytest

from sqlalchemy.exc import IntegrityError

from aurweb import db
from aurweb.models.account_type import USER_ID
from aurweb.models.group import Group
from aurweb.models.package import Package
from aurweb.models.package_base import PackageBase
from aurweb.models.package_group import PackageGroup
from aurweb.models.user import User

user = group = pkgbase = package = None


@pytest.fixture(autouse=True)
def setup(db_test):
    global user, group, pkgbase, package

    with db.begin():
        user = db.create(User, Username="test", Email="test@example.org",
                         RealName="Test User", Passwd="testPassword",
                         AccountTypeID=USER_ID)
        group = db.create(Group, Name="Test Group")

    with db.begin():
        pkgbase = db.create(PackageBase, Name="test-package", Maintainer=user)
        package = db.create(Package, PackageBase=pkgbase, Name=pkgbase.Name)


def test_package_group():
    with db.begin():
        package_group = db.create(PackageGroup, Package=package, Group=group)
    assert package_group.Group == group
    assert package_group.Package == package


def test_package_group_null_package_raises_exception():
    with pytest.raises(IntegrityError):
        PackageGroup(Group=group)


def test_package_group_null_group_raises_exception():
    with pytest.raises(IntegrityError):
        PackageGroup(Package=package)
