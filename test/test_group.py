import pytest

from sqlalchemy.exc import IntegrityError

from aurweb.db import create
from aurweb.models.group import Group
from aurweb.testing import setup_test_db


@pytest.fixture(autouse=True)
def setup():
    setup_test_db("Groups")


def test_group_creation():
    group = create(Group, Name="Test Group")
    assert bool(group.ID)
    assert group.Name == "Test Group"


def test_group_null_name_raises_exception():
    from aurweb.db import session
    with pytest.raises(IntegrityError):
        create(Group)
    session.rollback()
