import pytest

from aurweb.db import create, delete
from aurweb.models.request_type import RequestType
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
