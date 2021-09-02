import pytest

from sqlalchemy.exc import IntegrityError

from aurweb import db
from aurweb.models.group import Group
from aurweb.testing import setup_test_db


@pytest.fixture(autouse=True)
def setup():
    setup_test_db("Groups")


def test_group_creation():
    with db.begin():
        group = db.create(Group, Name="Test Group")
    assert bool(group.ID)
    assert group.Name == "Test Group"


def test_group_null_name_raises_exception():
    with pytest.raises(IntegrityError):
        with db.begin():
            db.create(Group)
    db.rollback()
