from datetime import datetime

import pytest

from sqlalchemy.exc import IntegrityError

from aurweb import db
from aurweb.models.account_type import USER_ID
from aurweb.models.package_base import PackageBase
from aurweb.models.package_request import (ACCEPTED, ACCEPTED_ID, CLOSED, CLOSED_ID, PENDING, PENDING_ID, REJECTED,
                                           REJECTED_ID, PackageRequest)
from aurweb.models.request_type import MERGE_ID
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
def pkgbase(user: User) -> PackageBase:
    with db.begin():
        pkgbase = db.create(PackageBase, Name="test-package", Maintainer=user)
    yield pkgbase


def test_package_request_creation(user: User, pkgbase: PackageBase):
    with db.begin():
        package_request = db.create(PackageRequest, ReqTypeID=MERGE_ID,
                                    User=user, PackageBase=pkgbase,
                                    PackageBaseName=pkgbase.Name,
                                    Comments=str(), ClosureComment=str())

    assert bool(package_request.ID)
    assert package_request.User == user
    assert package_request.PackageBase == pkgbase
    assert package_request.PackageBaseName == pkgbase.Name
    assert package_request.Comments == str()
    assert package_request.ClosureComment == str()

    # Make sure that everything is cross-referenced with relationships.
    assert package_request in user.package_requests
    assert package_request in pkgbase.requests


def test_package_request_closed(user: User, pkgbase: PackageBase):
    ts = int(datetime.utcnow().timestamp())
    with db.begin():
        package_request = db.create(PackageRequest, ReqTypeID=MERGE_ID,
                                    User=user, PackageBase=pkgbase,
                                    PackageBaseName=pkgbase.Name,
                                    Closer=user, ClosedTS=ts,
                                    Comments=str(), ClosureComment=str())

    assert package_request.Closer == user
    assert package_request.ClosedTS == ts

    # Test relationships.
    assert package_request in user.closed_requests


def test_package_request_null_request_type_raises(user: User,
                                                  pkgbase: PackageBase):
    with pytest.raises(IntegrityError):
        PackageRequest(User=user, PackageBase=pkgbase,
                       PackageBaseName=pkgbase.Name,
                       Comments=str(), ClosureComment=str())


def test_package_request_null_user_raises(pkgbase: PackageBase):
    with pytest.raises(IntegrityError):
        PackageRequest(ReqTypeID=MERGE_ID,
                       PackageBase=pkgbase, PackageBaseName=pkgbase.Name,
                       Comments=str(), ClosureComment=str())


def test_package_request_null_package_base_raises(user: User,
                                                  pkgbase: PackageBase):
    with pytest.raises(IntegrityError):
        PackageRequest(ReqTypeID=MERGE_ID,
                       User=user, PackageBaseName=pkgbase.Name,
                       Comments=str(), ClosureComment=str())


def test_package_request_null_package_base_name_raises(user: User,
                                                       pkgbase: PackageBase):
    with pytest.raises(IntegrityError):
        PackageRequest(ReqTypeID=MERGE_ID,
                       User=user, PackageBase=pkgbase,
                       Comments=str(), ClosureComment=str())


def test_package_request_null_comments_raises(user: User,
                                              pkgbase: PackageBase):
    with pytest.raises(IntegrityError):
        PackageRequest(ReqTypeID=MERGE_ID, User=user,
                       PackageBase=pkgbase, PackageBaseName=pkgbase.Name,
                       ClosureComment=str())


def test_package_request_null_closure_comment_raises(user: User,
                                                     pkgbase: PackageBase):
    with pytest.raises(IntegrityError):
        PackageRequest(ReqTypeID=MERGE_ID, User=user,
                       PackageBase=pkgbase, PackageBaseName=pkgbase.Name,
                       Comments=str())


def test_package_request_status_display(user: User, pkgbase: PackageBase):
    """ Test status_display() based on the Status column value. """
    with db.begin():
        pkgreq = db.create(PackageRequest, ReqTypeID=MERGE_ID,
                           User=user, PackageBase=pkgbase,
                           PackageBaseName=pkgbase.Name,
                           Comments=str(), ClosureComment=str(),
                           Status=PENDING_ID)
    assert pkgreq.status_display() == PENDING

    with db.begin():
        pkgreq.Status = CLOSED_ID
    assert pkgreq.status_display() == CLOSED

    with db.begin():
        pkgreq.Status = ACCEPTED_ID
    assert pkgreq.status_display() == ACCEPTED

    with db.begin():
        pkgreq.Status = REJECTED_ID
    assert pkgreq.status_display() == REJECTED

    with db.begin():
        pkgreq.Status = 124
    with pytest.raises(KeyError):
        pkgreq.status_display()
