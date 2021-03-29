import pytest

from aurweb.models.account_type import AccountType
from aurweb.testing import setup_test_db


@pytest.fixture(autouse=True)
def setup():
    setup_test_db()


def test_account_type():
    """ Test creating an AccountType, and reading its columns. """
    from aurweb.db import session
    account_type = AccountType(AccountType="TestUser")
    session.add(account_type)
    session.commit()

    # Make sure it got created and was given an ID.
    assert bool(account_type.ID)

    # Next, test our string functions.
    assert str(account_type) == "TestUser"
    assert repr(account_type) == \
        "<AccountType(ID='%s', AccountType='TestUser')>" % (
        account_type.ID)

    session.delete(account_type)
