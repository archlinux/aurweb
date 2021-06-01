import pytest

from aurweb.db import create, delete, query
from aurweb.models.relation_type import RelationType
from aurweb.testing import setup_test_db


@pytest.fixture(autouse=True)
def setup():
    setup_test_db()


def test_relation_type_creation():
    relation_type = create(RelationType, Name="test-relation")
    assert bool(relation_type.ID)
    assert relation_type.Name == "test-relation"

    delete(RelationType, RelationType.ID == relation_type.ID)


def test_relation_types():
    conflicts = query(RelationType, RelationType.Name == "conflicts").first()
    assert conflicts is not None
    assert conflicts.Name == "conflicts"

    provides = query(RelationType, RelationType.Name == "provides").first()
    assert provides is not None
    assert provides.Name == "provides"

    replaces = query(RelationType, RelationType.Name == "replaces").first()
    assert replaces is not None
    assert replaces.Name == "replaces"
