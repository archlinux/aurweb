from datetime import datetime

import pytest

from sqlalchemy.exc import IntegrityError

from aurweb.db import create, rollback
from aurweb.models.package_base import PackageBase
from aurweb.models.package_vote import PackageVote
from aurweb.models.user import User
from aurweb.testing import setup_test_db

user = pkgbase = None


@pytest.fixture(autouse=True)
def setup():
    global user, pkgbase

    setup_test_db("Users", "PackageBases", "PackageVotes")

    user = create(User, Username="test", Email="test@example.org",
                  RealName="Test User", Passwd="testPassword")
    pkgbase = create(PackageBase, Name="test-package", Maintainer=user)


def test_package_vote_creation():
    ts = int(datetime.utcnow().timestamp())
    package_vote = create(PackageVote, User=user, PackageBase=pkgbase,
                          VoteTS=ts)
    assert bool(package_vote)
    assert package_vote.User == user
    assert package_vote.PackageBase == pkgbase
    assert package_vote.VoteTS == ts


def test_package_vote_null_user_raises_exception():
    with pytest.raises(IntegrityError):
        create(PackageVote, PackageBase=pkgbase, VoteTS=1)
    rollback()


def test_package_vote_null_pkgbase_raises_exception():
    with pytest.raises(IntegrityError):
        create(PackageVote, User=user, VoteTS=1)
    rollback()


def test_package_vote_null_votets_raises_exception():
    with pytest.raises(IntegrityError):
        create(PackageVote, User=user, PackageBase=pkgbase)
    rollback()
