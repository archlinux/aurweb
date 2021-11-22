from datetime import datetime

import pytest

from aurweb import db
from aurweb.models import User
from aurweb.models.account_type import USER_ID
from aurweb.scripts import usermaint


@pytest.fixture(autouse=True)
def setup(db_test):
    return


@pytest.fixture
def user() -> User:
    with db.begin():
        user = db.create(User, Username="test", Email="test@example.org",
                         Passwd="testPassword", AccountTypeID=USER_ID)
    yield user


def test_usermaint_noop(user: User):
    """ Last[SSH]Login isn't expired in this test: usermaint is noop. """

    now = int(datetime.utcnow().timestamp())
    with db.begin():
        user.LastLoginIPAddress = "127.0.0.1"
        user.LastLogin = now - 10
        user.LastSSHLoginIPAddress = "127.0.0.1"
        user.LastSSHLogin = now - 10

    usermaint.main()

    assert user.LastLoginIPAddress == "127.0.0.1"
    assert user.LastSSHLoginIPAddress == "127.0.0.1"


def test_usermaint(user: User):
    """
    In this case, we first test that only the expired record gets
    updated, but the non-expired record remains untouched. After,
    we update the login time on the non-expired record and exercise
    its code path.
    """

    now = int(datetime.utcnow().timestamp())
    limit_to = now - 86400 * 7
    with db.begin():
        user.LastLoginIPAddress = "127.0.0.1"
        user.LastLogin = limit_to - 666
        user.LastSSHLoginIPAddress = "127.0.0.1"
        user.LastSSHLogin = now - 10

    usermaint.main()

    assert user.LastLoginIPAddress is None
    assert user.LastSSHLoginIPAddress == "127.0.0.1"

    with db.begin():
        user.LastSSHLogin = limit_to - 666

    usermaint.main()

    assert user.LastLoginIPAddress is None
    assert user.LastSSHLoginIPAddress is None
