import pytest

from sqlalchemy.exc import IntegrityError

from aurweb.db import create, delete, get_engine
from aurweb.models.group import Group


def test_group_creation():
    get_engine()
    group = create(Group, Name="Test Group")
    assert bool(group.ID)
    assert group.Name == "Test Group"
    delete(Group, Group.ID == group.ID)


def test_group_null_name_raises_exception():
    from aurweb.db import session
    with pytest.raises(IntegrityError):
        create(Group)
    session.rollback()
