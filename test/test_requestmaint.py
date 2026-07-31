from collections.abc import Generator

import pytest

from aurweb import config, db, time
from aurweb.models import PackageBase, PackageRequest, User
from aurweb.models.account_type import USER_ID
from aurweb.models.package_request import PENDING_ID, REJECTED_ID
from aurweb.models.request_type import ADOPTION_ID, ORPHAN_ID
from aurweb.scripts import requestmaint


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
            Passwd="testPassword",
            AccountTypeID=USER_ID,
        )
    yield user


@pytest.fixture
def pkgbase(user: User) -> Generator[PackageBase]:
    now = time.utcnow()
    with db.begin():
        pkgbase = db.create(
            PackageBase,
            Name="test-package",
            SubmittedTS=now,
            ModifiedTS=now,
        )
    yield pkgbase


def make_request(
    user: User, pkgbase: PackageBase, reqtype_id: int, age: int
) -> PackageRequest:
    with db.begin():
        pkgreq = db.create(
            PackageRequest,
            ReqTypeID=reqtype_id,
            User=user,
            PackageBase=pkgbase,
            PackageBaseName=pkgbase.Name,
            RequestTS=time.utcnow() - age,
            Status=PENDING_ID,
            Comments=str(),
            ClosureComment=str(),
        )
    return pkgreq


def test_requestmaint_noop(user: User, pkgbase: PackageBase):
    """A fresh adoption request is left alone."""

    pkgreq = make_request(user, pkgbase, ADOPTION_ID, age=10)

    requestmaint.main()

    assert pkgreq.Status == PENDING_ID
    assert pkgreq.ClosedTS is None


def test_requestmaint_rejects_idle_adoption(user: User, pkgbase: PackageBase):
    idle_time = config.getint("options", "request_idle_time")
    pkgreq = make_request(user, pkgbase, ADOPTION_ID, age=idle_time + 666)

    requestmaint.main()

    assert pkgreq.Status == REJECTED_ID
    assert pkgreq.ClosedTS is not None
    assert "Rejected adoption for test-package" in pkgreq.ClosureComment


def test_requestmaint_rejects_request_with_deleted_requester(
    user: User, pkgbase: PackageBase
):
    idle_time = config.getint("options", "request_idle_time")
    pkgreq = make_request(user, pkgbase, ADOPTION_ID, age=idle_time + 666)
    with db.begin():
        pkgreq.User = None

    requestmaint.main()

    assert pkgreq.UsersID is None
    assert pkgreq.Status == REJECTED_ID


def test_requestmaint_leaves_other_types(user: User, pkgbase: PackageBase):
    idle_time = config.getint("options", "request_idle_time")
    pkgreq = make_request(user, pkgbase, ORPHAN_ID, age=idle_time + 666)

    requestmaint.main()

    assert pkgreq.Status == PENDING_ID


def test_requestmaint_leaves_closed_requests(user: User, pkgbase: PackageBase):
    idle_time = config.getint("options", "request_idle_time")
    pkgreq = make_request(user, pkgbase, ADOPTION_ID, age=idle_time + 666)
    with db.begin():
        pkgreq.Status = REJECTED_ID
        pkgreq.ClosureComment = "Closed by a human."

    requestmaint.main()

    assert pkgreq.ClosureComment == "Closed by a human."
