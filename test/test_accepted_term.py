import pytest

from sqlalchemy.exc import IntegrityError

from aurweb.db import create, delete, query
from aurweb.models.accepted_term import AcceptedTerm
from aurweb.models.account_type import AccountType
from aurweb.models.term import Term
from aurweb.models.user import User
from aurweb.testing import setup_test_db

user, term, accepted_term = None, None, None


@pytest.fixture(autouse=True)
def setup():
    global user, term, accepted_term

    setup_test_db("Users", "AcceptedTerms", "Terms")

    account_type = query(AccountType,
                         AccountType.AccountType == "User").first()
    user = create(User, Username="test", Email="test@example.org",
                  RealName="Test User", Passwd="testPassword",
                  account_type=account_type)

    term = create(Term, Description="Test term", URL="https://test.term")

    yield term

    delete(Term, Term.ID == term.ID)
    delete(User, User.ID == user.ID)


def test_accepted_term():
    accepted_term = create(AcceptedTerm, User=user, Term=term)

    # Make sure our AcceptedTerm relationships got initialized properly.
    assert accepted_term.User == user
    assert accepted_term in user.accepted_terms
    assert accepted_term in term.accepted

    delete(AcceptedTerm, AcceptedTerm.User == user, AcceptedTerm.Term == term)


def test_accepted_term_null_user_raises_exception():
    from aurweb.db import session
    with pytest.raises(IntegrityError):
        create(AcceptedTerm, Term=term)
    session.rollback()


def test_accepted_term_null_term_raises_exception():
    from aurweb.db import session
    with pytest.raises(IntegrityError):
        create(AcceptedTerm, User=user)
    session.rollback()
