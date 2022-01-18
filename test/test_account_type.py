import pytest

from aurweb import db
from aurweb.models.account_type import AccountType
from aurweb.models.user import User


@pytest.fixture(autouse=True)
def setup(db_test):
    return


@pytest.fixture
def account_type() -> AccountType:
    with db.begin():
        account_type_ = db.create(AccountType, AccountType="TestUser")

    yield account_type_

    with db.begin():
        db.delete(account_type_)


def test_account_type(account_type):
    """ Test creating an AccountType, and reading its columns. """
    # Make sure it got db.created and was given an ID.
    assert bool(account_type.ID)

    # Next, test our string functions.
    assert str(account_type) == "TestUser"
    assert repr(account_type) == \
        "<AccountType(ID='%s', AccountType='TestUser')>" % (
        account_type.ID)

    record = db.query(AccountType,
                      AccountType.AccountType == "TestUser").first()
    assert account_type == record


def test_user_account_type_relationship(account_type):
    with db.begin():
        user = db.create(User, Username="test", Email="test@example.org",
                         RealName="Test User", Passwd="testPassword",
                         AccountType=account_type)

    assert user.AccountType == account_type

    # This must be db.deleted here to avoid foreign key issues when
    # deleting the temporary AccountType in the fixture.
    with db.begin():
        db.delete(user)
