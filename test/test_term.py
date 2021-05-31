import pytest

from sqlalchemy.exc import IntegrityError

from aurweb.db import create, delete
from aurweb.models.term import Term


def test_term_creation():
    term = create(Term, Description="Term description",
                  URL="https://fake_url.io")
    assert bool(term.ID)
    assert term.Description == "Term description"
    assert term.URL == "https://fake_url.io"
    assert term.Revision == 1
    delete(Term, Term.ID == term.ID)


def test_term_null_description_raises_exception():
    from aurweb.db import session
    with pytest.raises(IntegrityError):
        create(Term, URL="https://fake_url.io")
    session.rollback()


def test_term_null_url_raises_exception():
    from aurweb.db import session
    with pytest.raises(IntegrityError):
        create(Term, Description="Term description")
    session.rollback()
