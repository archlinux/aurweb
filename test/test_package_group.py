import pytest

from sqlalchemy.exc import IntegrityError

from aurweb import db
from aurweb.models.account_type import USER_ID
from aurweb.models.group import Group
from aurweb.models.package import Package
from aurweb.models.package_base import PackageBase
from aurweb.models.package_group import PackageGroup
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
def group() -> Group:
    with db.begin():
        group = db.create(Group, Name="Test Group")
    yield group


@pytest.fixture
def package(user: User) -> Package:
    with db.begin():
        pkgbase = db.create(PackageBase, Name="test-package", Maintainer=user)
        package = db.create(Package, PackageBase=pkgbase, Name=pkgbase.Name)
    yield package


def test_package_group(package: Package, group: Group):
    with db.begin():
        package_group = db.create(PackageGroup, Package=package, Group=group)
    assert package_group.Group == group
    assert package_group.Package == package


def test_package_group_null_package_raises(group: Group):
    with pytest.raises(IntegrityError):
        PackageGroup(Group=group)


def test_package_group_null_group_raises(package: Package):
    with pytest.raises(IntegrityError):
        PackageGroup(Package=package)
