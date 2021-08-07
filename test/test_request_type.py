import pytest

from aurweb.db import create, delete, query
from aurweb.models.request_type import DELETION_ID, MERGE_ID, ORPHAN_ID, RequestType
from aurweb.testing import setup_test_db


@pytest.fixture(autouse=True)
def setup():
    setup_test_db()


def test_request_type_creation():
    request_type = create(RequestType, Name="Test Request")
    assert bool(request_type.ID)
    assert request_type.Name == "Test Request"
    delete(RequestType, RequestType.ID == request_type.ID)


def test_request_type_null_name_returns_empty_string():
    request_type = create(RequestType)
    assert bool(request_type.ID)
    assert request_type.Name == str()
    delete(RequestType, RequestType.ID == request_type.ID)


def test_request_type_name_display():
    deletion = query(RequestType, RequestType.ID == DELETION_ID).first()
    assert deletion.name_display() == "Deletion"

    orphan = query(RequestType, RequestType.ID == ORPHAN_ID).first()
    assert orphan.name_display() == "Orphan"

    merge = query(RequestType, RequestType.ID == MERGE_ID).first()
    assert merge.name_display() == "Merge"
