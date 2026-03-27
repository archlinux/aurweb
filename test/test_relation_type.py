import pytest
from sqlalchemy import select

from aurweb import db
from aurweb.models.relation_type import RelationType


@pytest.fixture(autouse=True)
def setup(db_test):
    return


def test_relation_type_creation() -> None:
    with db.begin():
        relation_type = db.create(RelationType, Name="test-relation")

    assert bool(relation_type.ID)
    assert relation_type.Name == "test-relation"

    with db.begin():
        db.delete(relation_type)


def test_relation_types() -> None:
    conflicts = (
        db.get_session()
        .execute(select(RelationType).where(RelationType.Name == "conflicts"))
        .scalars()
        .first()
    )
    assert conflicts is not None
    assert conflicts.Name == "conflicts"

    provides = (
        db.get_session()
        .execute(select(RelationType).where(RelationType.Name == "provides"))
        .scalars()
        .first()
    )
    assert provides is not None
    assert provides.Name == "provides"

    replaces = (
        db.get_session()
        .execute(select(RelationType).where(RelationType.Name == "replaces"))
        .scalars()
        .first()
    )
    assert replaces is not None
    assert replaces.Name == "replaces"
