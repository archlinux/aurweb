import pytest

from aurweb.models.account_type import AccountType
from aurweb.models.user import User
from aurweb.testing import setup_test_db


@pytest.fixture(autouse=True)
def setup():
    setup_test_db("Users")


def test_user():
    """ Test creating a user and reading its columns. """
    from aurweb.db import session

    # First, grab our target AccountType.
    account_type = session.query(AccountType).filter(
        AccountType.AccountType == "User").first()

    user = User(
        AccountType=account_type,
        RealName="Test User", Username="test",
        Email="test@example.org", Passwd="abcd",
        IRCNick="tester",
        Salt="efgh", ResetKey="blahblah")
    session.add(user)
    session.commit()

    assert user in account_type.users

    # Make sure the user was created and given an ID.
    assert bool(user.ID)

    # Search for the user via query API.
    result = session.query(User).filter(User.ID == user.ID).first()

    # Compare the result and our original user.
    assert result.ID == user.ID
    assert result.AccountType.ID == user.AccountType.ID
    assert result.Username == user.Username
    assert result.Email == user.Email

    # Ensure we've got the correct account type.
    assert user.AccountType.ID == account_type.ID
    assert user.AccountType.AccountType == account_type.AccountType

    # Test out user string functions.
    assert repr(user) == f"<User(ID='{user.ID}', " + \
        "AccountType='User', Username='test')>"

    session.delete(user)
