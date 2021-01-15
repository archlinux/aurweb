import pytest

from aurweb.models.account_type import AccountType
from aurweb.models.user import User
from aurweb.testing import setup_test_db
from aurweb.testing.models import make_user

account_type = None


@pytest.fixture(autouse=True)
def setup():
    setup_test_db("Users")

    from aurweb.db import session

    global account_type

    account_type = AccountType(AccountType="TestUser")
    session.add(account_type)
    session.commit()

    yield account_type

    session.delete(account_type)
    session.commit()


def test_account_type():
    """ Test creating an AccountType, and reading its columns. """
    from aurweb.db import session

    # Make sure it got created and was given an ID.
    assert bool(account_type.ID)

    # Next, test our string functions.
    assert str(account_type) == "TestUser"
    assert repr(account_type) == \
        "<AccountType(ID='%s', AccountType='TestUser')>" % (
        account_type.ID)

    record = session.query(AccountType).filter(
        AccountType.AccountType == "TestUser").first()
    assert account_type == record


def test_user_account_type_relationship():
    from aurweb.db import session

    user = make_user(Username="test", Email="test@example.org",
                     RealName="Test User", Passwd="testPassword",
                     AccountType=account_type)

    assert user.AccountType == account_type
    assert account_type.users.filter(User.ID == user.ID).first()

    session.delete(user)
    session.commit()
