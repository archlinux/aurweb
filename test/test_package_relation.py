import pytest

from sqlalchemy.exc import IntegrityError, OperationalError

from aurweb import db
from aurweb.db import create, query
from aurweb.models.account_type import AccountType
from aurweb.models.package import Package
from aurweb.models.package_base import PackageBase
from aurweb.models.package_relation import PackageRelation
from aurweb.models.relation_type import RelationType
from aurweb.models.user import User
from aurweb.testing import setup_test_db

user = pkgbase = package = None


@pytest.fixture(autouse=True)
def setup():
    global user, pkgbase, package

    setup_test_db("Users", "PackageBases", "Packages", "PackageRelations")

    account_type = query(AccountType,
                         AccountType.AccountType == "User").first()

    with db.begin():
        user = create(User, Username="test", Email="test@example.org",
                      RealName="Test User", Passwd="testPassword",
                      AccountType=account_type)
        pkgbase = create(PackageBase,
                         Name="test-package",
                         Maintainer=user)
        package = create(Package,
                         PackageBase=pkgbase,
                         Name=pkgbase.Name,
                         Description="Test description.",
                         URL="https://test.package")


def test_package_relation():
    conflicts = query(RelationType, RelationType.Name == "conflicts").first()

    with db.begin():
        pkgrel = create(PackageRelation, Package=package,
                        RelationType=conflicts,
                        RelName="test-relation")
    assert pkgrel.RelName == "test-relation"
    assert pkgrel.Package == package
    assert pkgrel.RelationType == conflicts
    assert pkgrel in conflicts.package_relations
    assert pkgrel in package.package_relations

    provides = query(RelationType, RelationType.Name == "provides").first()
    with db.begin():
        pkgrel.RelationType = provides
    assert pkgrel.RelName == "test-relation"
    assert pkgrel.Package == package
    assert pkgrel.RelationType == provides
    assert pkgrel in provides.package_relations
    assert pkgrel in package.package_relations

    replaces = query(RelationType, RelationType.Name == "replaces").first()
    with db.begin():
        pkgrel.RelationType = replaces
    assert pkgrel.RelName == "test-relation"
    assert pkgrel.Package == package
    assert pkgrel.RelationType == replaces
    assert pkgrel in replaces.package_relations
    assert pkgrel in package.package_relations


def test_package_relation_null_package_raises_exception():
    conflicts = query(RelationType, RelationType.Name == "conflicts").first()
    assert conflicts is not None

    with pytest.raises(IntegrityError):
        with db.begin():
            create(PackageRelation,
                   RelationType=conflicts,
                   RelName="test-relation")
    db.rollback()


def test_package_relation_null_relation_type_raises_exception():
    with pytest.raises(IntegrityError):
        with db.begin():
            create(PackageRelation,
                   Package=package,
                   RelName="test-relation")
    db.rollback()


def test_package_relation_null_relname_raises_exception():
    depends = query(RelationType, RelationType.Name == "conflicts").first()
    assert depends is not None

    with pytest.raises((OperationalError, IntegrityError)):
        with db.begin():
            create(PackageRelation,
                   Package=package,
                   RelationType=depends)
    db.rollback()
