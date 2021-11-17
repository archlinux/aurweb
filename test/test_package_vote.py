from datetime import datetime

import pytest

from sqlalchemy.exc import IntegrityError

from aurweb import db
from aurweb.models.package_base import PackageBase
from aurweb.models.package_vote import PackageVote
from aurweb.models.user import User

user = pkgbase = None


@pytest.fixture(autouse=True)
def setup(db_test):
    global user, pkgbase

    with db.begin():
        user = db.create(User, Username="test", Email="test@example.org",
                         RealName="Test User", Passwd="testPassword")
        pkgbase = db.create(PackageBase, Name="test-package", Maintainer=user)


def test_package_vote_creation():
    ts = int(datetime.utcnow().timestamp())

    with db.begin():
        package_vote = db.create(PackageVote, User=user,
                                 PackageBase=pkgbase, VoteTS=ts)
    assert bool(package_vote)
    assert package_vote.User == user
    assert package_vote.PackageBase == pkgbase
    assert package_vote.VoteTS == ts


def test_package_vote_null_user_raises_exception():
    with pytest.raises(IntegrityError):
        PackageVote(PackageBase=pkgbase, VoteTS=1)


def test_package_vote_null_pkgbase_raises_exception():
    with pytest.raises(IntegrityError):
        PackageVote(User=user, VoteTS=1)


def test_package_vote_null_votets_raises_exception():
    with pytest.raises(IntegrityError):
        PackageVote(User=user, PackageBase=pkgbase)
