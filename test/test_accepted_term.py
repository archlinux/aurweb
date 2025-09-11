from typing import Generator

import pytest
from sqlalchemy.exc import IntegrityError

from aurweb import db
from aurweb.models.accepted_term import AcceptedTerm
from aurweb.models.account_type import USER_ID
from aurweb.models.term import Term
from aurweb.models.user import User


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
            RealName="Test User",
            Passwd="testPassword",
            AccountTypeID=USER_ID,
        )
    yield user


@pytest.fixture
def term() -> Generator[Term]:
    with db.begin():
        term = db.create(Term, Description="Test term", URL="https://test.term")
    yield term


@pytest.fixture
def accepted_term(user: User, term: Term) -> Generator[AcceptedTerm]:
    with db.begin():
        accepted_term = db.create(AcceptedTerm, User=user, Term=term)
    yield accepted_term


def test_accepted_term(user: User, term: Term, accepted_term: AcceptedTerm):
    # Make sure our AcceptedTerm relationships got initialized properly.
    assert accepted_term.User == user
    assert accepted_term in user.accepted_terms
    assert accepted_term in term.accepted_terms


def test_accepted_term_null_user_raises_exception(term: Term):
    with pytest.raises(IntegrityError):
        AcceptedTerm(Term=term)


def test_accepted_term_null_term_raises_exception(user: User):
    with pytest.raises(IntegrityError):
        AcceptedTerm(User=user)
