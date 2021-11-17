import pytest

from aurweb.db import begin, create, delete, query
from aurweb.models.dependency_type import DependencyType


@pytest.fixture(autouse=True)
def setup(db_test):
    return


def test_dependency_types():
    dep_types = ["depends", "makedepends", "checkdepends", "optdepends"]
    for dep_type in dep_types:
        dependency_type = query(DependencyType,
                                DependencyType.Name == dep_type).first()
        assert dependency_type is not None


def test_dependency_type_creation():
    with begin():
        dependency_type = create(DependencyType, Name="Test Type")
    assert bool(dependency_type.ID)
    assert dependency_type.Name == "Test Type"
    with begin():
        delete(dependency_type)


def test_dependency_type_null_name_uses_default():
    with begin():
        dependency_type = create(DependencyType)
    assert dependency_type.Name == str()
    with begin():
        delete(dependency_type)
