import pytest
from sqlalchemy.exc import IntegrityError

from aurweb import db
from aurweb.models.group import Group


@pytest.fixture(autouse=True)
def setup(db_test):
    return


def test_group_creation() -> None:
    with db.begin():
        group = db.create(Group, Name="Test Group")
    assert bool(group.ID)
    assert group.Name == "Test Group"


def test_group_null_name_raises_exception() -> None:
    with pytest.raises(IntegrityError):
        Group()
