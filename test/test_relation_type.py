import pytest

from aurweb import db
from aurweb.models.relation_type import RelationType


@pytest.fixture(autouse=True)
def setup(db_test):
    return


def test_relation_type_creation():
    with db.begin():
        relation_type = db.create(RelationType, Name="test-relation")

    assert bool(relation_type.ID)
    assert relation_type.Name == "test-relation"

    with db.begin():
        db.delete(relation_type)


def test_relation_types():
    conflicts = db.query(RelationType, RelationType.Name == "conflicts").first()
    assert conflicts is not None
    assert conflicts.Name == "conflicts"

    provides = db.query(RelationType, RelationType.Name == "provides").first()
    assert provides is not None
    assert provides.Name == "provides"

    replaces = db.query(RelationType, RelationType.Name == "replaces").first()
    assert replaces is not None
    assert replaces.Name == "replaces"
