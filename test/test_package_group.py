import pytest

from sqlalchemy.exc import IntegrityError

from aurweb.db import create, query
from aurweb.models.account_type import AccountType
from aurweb.models.group import Group
from aurweb.models.package import Package
from aurweb.models.package_base import PackageBase
from aurweb.models.package_group import PackageGroup
from aurweb.models.user import User
from aurweb.testing import setup_test_db

user = group = pkgbase = package = None


@pytest.fixture(autouse=True)
def setup():
    global user, group, pkgbase, package

    setup_test_db("Users", "PackageBases", "Packages",
                  "Groups", "PackageGroups")

    account_type = query(AccountType,
                         AccountType.AccountType == "User").first()
    user = create(User, Username="test", Email="test@example.org",
                  RealName="Test User", Passwd="testPassword",
                  account_type=account_type)

    group = create(Group, Name="Test Group")
    pkgbase = create(PackageBase, Name="test-package", Maintainer=user)
    package = create(Package, PackageBase=pkgbase, Name=pkgbase.Name)


def test_package_group():
    package_group = create(PackageGroup, Package=package, Group=group)
    assert package_group.Group == group
    assert package_group.Package == package


def test_package_group_null_package_raises_exception():
    from aurweb.db import session
    with pytest.raises(IntegrityError):
        create(PackageGroup, Group=group)
    session.rollback()


def test_package_group_null_group_raises_exception():
    from aurweb.db import session
    with pytest.raises(IntegrityError):
        create(PackageGroup, Package=package)
    session.rollback()
