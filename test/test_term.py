import pytest

from sqlalchemy.exc import IntegrityError

from aurweb import db
from aurweb.models.term import Term
from aurweb.testing import setup_test_db


@pytest.fixture(autouse=True)
def setup():
    setup_test_db("Terms")

    yield None

    # Wipe em out just in case records are leftover.
    setup_test_db("Terms")


def test_term_creation():
    with db.begin():
        term = db.create(Term, Description="Term description",
                         URL="https://fake_url.io")
    assert bool(term.ID)
    assert term.Description == "Term description"
    assert term.URL == "https://fake_url.io"
    assert term.Revision == 1


def test_term_null_description_raises_exception():
    with pytest.raises(IntegrityError):
        with db.begin():
            db.create(Term, URL="https://fake_url.io")
    db.rollback()


def test_term_null_url_raises_exception():
    with pytest.raises(IntegrityError):
        with db.begin():
            db.create(Term, Description="Term description")
    db.rollback()
