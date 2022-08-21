import pytest
from sqlalchemy.exc import IntegrityError

from aurweb import db
from aurweb.models.term import Term


@pytest.fixture(autouse=True)
def setup(db_test):
    return


def test_term_creation():
    with db.begin():
        term = db.create(
            Term, Description="Term description", URL="https://fake_url.io"
        )
    assert bool(term.ID)
    assert term.Description == "Term description"
    assert term.URL == "https://fake_url.io"
    assert term.Revision == 1


def test_term_null_description_raises_exception():
    with pytest.raises(IntegrityError):
        Term(URL="https://fake_url.io")


def test_term_null_url_raises_exception():
    with pytest.raises(IntegrityError):
        Term(Description="Term description")
