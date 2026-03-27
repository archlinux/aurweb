import pytest
from sqlalchemy import select

from aurweb import db
from aurweb.db import begin, create, delete
from aurweb.models.dependency_type import DependencyType


@pytest.fixture(autouse=True)
def setup(db_test):
    return


def test_dependency_types() -> None:
    dep_types = ["depends", "makedepends", "checkdepends", "optdepends"]
    for dep_type in dep_types:
        dependency_type = (
            db.get_session()
            .execute(select(DependencyType).where(DependencyType.Name == dep_type))
            .scalars()
            .first()
        )
        assert dependency_type is not None


def test_dependency_type_creation() -> None:
    with begin():
        dependency_type = create(DependencyType, Name="Test Type")
    assert bool(dependency_type.ID)
    assert dependency_type.Name == "Test Type"
    with begin():
        delete(dependency_type)


def test_dependency_type_null_name_uses_default() -> None:
    with begin():
        dependency_type = create(DependencyType)
    assert dependency_type.Name == str()
    with begin():
        delete(dependency_type)
