import pytest

from sqlalchemy.exc import IntegrityError

from aurweb.db import create
from aurweb.models.term import Term
from aurweb.testing import setup_test_db


@pytest.fixture(autouse=True)
def setup():
    setup_test_db("Terms")

    yield None

    # Wipe em out just in case records are leftover.
    setup_test_db("Terms")


def test_term_creation():
    term = create(Term, Description="Term description",
                  URL="https://fake_url.io")
    assert bool(term.ID)
    assert term.Description == "Term description"
    assert term.URL == "https://fake_url.io"
    assert term.Revision == 1


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
