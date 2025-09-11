from typing import Generator

import pytest
from sqlalchemy.exc import IntegrityError

from aurweb import db, time
from aurweb.models.account_type import USER_ID
from aurweb.models.package_base import PackageBase
from aurweb.models.package_vote import PackageVote
from aurweb.models.user import User


@pytest.fixture(autouse=True)
def setup(db_test):
    return


@pytest.fixture
def user() -> Generator[User]:
    with db.begin():
        user = db.create(
            User,
            Username="test",
            Email="test@example.org",
            RealName="Test User",
            Passwd=str(),
            AccountTypeID=USER_ID,
        )
    yield user


@pytest.fixture
def pkgbase(user: User) -> Generator[PackageBase]:
    with db.begin():
        pkgbase = db.create(PackageBase, Name="test-package", Maintainer=user)
    yield pkgbase


def test_package_vote_creation(user: User, pkgbase: PackageBase):
    ts = time.utcnow()

    with db.begin():
        package_vote = db.create(PackageVote, User=user, PackageBase=pkgbase, VoteTS=ts)
    assert bool(package_vote)
    assert package_vote.User == user
    assert package_vote.PackageBase == pkgbase
    assert package_vote.VoteTS == ts


def test_package_vote_null_user_raises(pkgbase: PackageBase):
    with pytest.raises(IntegrityError):
        PackageVote(PackageBase=pkgbase, VoteTS=1)


def test_package_vote_null_pkgbase_raises(user: User):
    with pytest.raises(IntegrityError):
        PackageVote(User=user, VoteTS=1)


def test_package_vote_null_votets_raises(user: User, pkgbase: PackageBase):
    with pytest.raises(IntegrityError):
        PackageVote(User=user, PackageBase=pkgbase)
