import pytest

from sqlalchemy.exc import IntegrityError

from aurweb import db
from aurweb.models.license import License
from aurweb.testing import setup_test_db


@pytest.fixture(autouse=True)
def setup():
    setup_test_db("Licenses")


def test_license_creation():
    with db.begin():
        license = db.create(License, Name="Test License")
    assert bool(license.ID)
    assert license.Name == "Test License"


def test_license_null_name_raises_exception():
    with pytest.raises(IntegrityError):
        with db.begin():
            db.create(License)
    db.rollback()
