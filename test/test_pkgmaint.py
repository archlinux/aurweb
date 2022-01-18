from typing import List

import pytest

from aurweb import db, time
from aurweb.models import Package, PackageBase, User
from aurweb.models.account_type import USER_ID
from aurweb.scripts import pkgmaint


@pytest.fixture(autouse=True)
def setup(db_test):
    return


@pytest.fixture
def user() -> User:
    with db.begin():
        user = db.create(User, Username="test", Email="test@example.org",
                         Passwd="testPassword", AccountTypeID=USER_ID)
    yield user


@pytest.fixture
def packages(user: User) -> List[Package]:
    output = []

    now = time.utcnow()
    with db.begin():
        for i in range(5):
            pkgbase = db.create(PackageBase, Name=f"pkg_{i}",
                                SubmittedTS=now,
                                ModifiedTS=now)
            pkg = db.create(Package, PackageBase=pkgbase,
                            Name=f"pkg_{i}", Version=f"{i}.0")
            output.append(pkg)
    yield output


def test_pkgmaint_noop(packages: List[Package]):
    assert len(packages) == 5
    pkgmaint.main()
    packages = db.query(Package).all()
    assert len(packages) == 5


def test_pkgmaint(packages: List[Package]):
    assert len(packages) == 5

    # Modify the first package so it's out of date and gets deleted.
    with db.begin():
        # Reduce SubmittedTS by a day + 10 seconds.
        packages[0].PackageBase.SubmittedTS -= (86400 + 10)

    # Run pkgmaint.
    pkgmaint.main()

    # Query package objects again and assert that the
    # first package was deleted but all others are intact.
    packages = db.query(Package).all()
    assert len(packages) == 4
    expected = ["pkg_1", "pkg_2", "pkg_3", "pkg_4"]
    for i, pkgname in enumerate(expected):
        assert packages[i].Name == pkgname
