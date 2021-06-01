import pytest

from aurweb.db import create, delete, query
from aurweb.models.dependency_type import DependencyType
from aurweb.testing import setup_test_db


@pytest.fixture(autouse=True)
def setup():
    setup_test_db()


def test_dependency_types():
    dep_types = ["depends", "makedepends", "checkdepends", "optdepends"]
    for dep_type in dep_types:
        dependency_type = query(DependencyType,
                                DependencyType.Name == dep_type).first()
        assert dependency_type is not None


def test_dependency_type_creation():
    dependency_type = create(DependencyType, Name="Test Type")
    assert bool(dependency_type.ID)
    assert dependency_type.Name == "Test Type"
    delete(DependencyType, DependencyType.ID == dependency_type.ID)


def test_dependency_type_null_name_uses_default():
    dependency_type = create(DependencyType)
    assert dependency_type.Name == str()
    delete(DependencyType, DependencyType.ID == dependency_type.ID)
