import pytest

from aurweb.db import begin, create, delete, query
from aurweb.models.account_type import AccountType
from aurweb.models.user import User
from aurweb.testing import setup_test_db

account_type = None


@pytest.fixture(autouse=True)
def setup():
    setup_test_db("Users")

    global account_type

    with begin():
        account_type = create(AccountType, AccountType="TestUser")

    yield account_type

    with begin():
        delete(AccountType, AccountType.ID == account_type.ID)


def test_account_type():
    """ Test creating an AccountType, and reading its columns. """
    # Make sure it got created and was given an ID.
    assert bool(account_type.ID)

    # Next, test our string functions.
    assert str(account_type) == "TestUser"
    assert repr(account_type) == \
        "<AccountType(ID='%s', AccountType='TestUser')>" % (
        account_type.ID)

    record = query(AccountType,
                   AccountType.AccountType == "TestUser").first()
    assert account_type == record


def test_user_account_type_relationship():
    with begin():
        user = create(User, Username="test", Email="test@example.org",
                      RealName="Test User", Passwd="testPassword",
                      AccountType=account_type)

    assert user.AccountType == account_type

    # This must be deleted here to avoid foreign key issues when
    # deleting the temporary AccountType in the fixture.
    with begin():
        delete(User, User.ID == user.ID)
