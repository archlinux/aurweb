import pytest
from sqlalchemy import select

from aurweb import db
from aurweb.models.request_type import DELETION_ID, MERGE_ID, ORPHAN_ID, RequestType


@pytest.fixture(autouse=True)
def setup(db_test):
    return


def test_request_type_creation() -> None:
    with db.begin():
        request_type = db.create(RequestType, Name="Test Request")

    assert bool(request_type.ID)
    assert request_type.Name == "Test Request"

    with db.begin():
        db.delete(request_type)


def test_request_type_null_name_returns_empty_string() -> None:
    with db.begin():
        request_type = db.create(RequestType)

    assert bool(request_type.ID)
    assert request_type.Name == str()

    with db.begin():
        db.delete(request_type)


def test_request_type_name_display() -> None:
    deletion = (
        db.get_session()
        .execute(select(RequestType).where(RequestType.ID == DELETION_ID))
        .scalars()
        .first()
    )
    assert deletion.name_display() == "Deletion"

    orphan = (
        db.get_session()
        .execute(select(RequestType).where(RequestType.ID == ORPHAN_ID))
        .scalars()
        .first()
    )
    assert orphan.name_display() == "Orphan"

    merge = (
        db.get_session()
        .execute(select(RequestType).where(RequestType.ID == MERGE_ID))
        .scalars()
        .first()
    )
    assert merge.name_display() == "Merge"
