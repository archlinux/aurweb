import pytest

from sqlalchemy.exc import IntegrityError

from aurweb import db
from aurweb.models.accepted_term import AcceptedTerm
from aurweb.models.account_type import USER_ID
from aurweb.models.term import Term
from aurweb.models.user import User

user = term = accepted_term = None


@pytest.fixture(autouse=True)
def setup(db_test):
    global user, term

    with db.begin():
        user = db.create(User, Username="test", Email="test@example.org",
                         RealName="Test User", Passwd="testPassword",
                         AccountTypeID=USER_ID)

        term = db.create(Term, Description="Test term",
                         URL="https://test.term")

    yield term


def test_accepted_term():
    with db.begin():
        accepted_term = db.create(AcceptedTerm, User=user, Term=term)

    # Make sure our AcceptedTerm relationships got initialized properly.
    assert accepted_term.User == user
    assert accepted_term in user.accepted_terms
    assert accepted_term in term.accepted_terms


def test_accepted_term_null_user_raises_exception():
    with pytest.raises(IntegrityError):
        AcceptedTerm(Term=term)


def test_accepted_term_null_term_raises_exception():
    with pytest.raises(IntegrityError):
        AcceptedTerm(User=user)
