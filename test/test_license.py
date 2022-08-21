import pytest
from sqlalchemy.exc import IntegrityError

from aurweb import db
from aurweb.models.license import License


@pytest.fixture(autouse=True)
def setup(db_test):
    return


def test_license_creation():
    with db.begin():
        license = db.create(License, Name="Test License")
    assert bool(license.ID)
    assert license.Name == "Test License"


def test_license_null_name_raises_exception():
    with pytest.raises(IntegrityError):
        License()
