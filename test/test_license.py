import pytest

from sqlalchemy.exc import IntegrityError

from aurweb.db import create
from aurweb.models.license import License
from aurweb.testing import setup_test_db


@pytest.fixture(autouse=True)
def setup():
    setup_test_db("Licenses")


def test_license_creation():
    license = create(License, Name="Test License")
    assert bool(license.ID)
    assert license.Name == "Test License"


def test_license_null_name_raises_exception():
    from aurweb.db import session
    with pytest.raises(IntegrityError):
        create(License)
    session.rollback()
