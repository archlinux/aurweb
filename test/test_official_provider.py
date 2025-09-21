import pytest
from sqlalchemy.exc import IntegrityError

from aurweb import db
from aurweb.models.official_provider import OfficialProvider


@pytest.fixture(autouse=True)
def setup(db_test):
    return


def test_official_provider_creation() -> None:
    with db.begin():
        oprovider = db.create(
            OfficialProvider,
            Name="some-name",
            Repo="some-repo",
            Provides="some-provides",
        )
    assert bool(oprovider.ID)
    assert oprovider.Name == "some-name"
    assert oprovider.Repo == "some-repo"
    assert oprovider.Provides == "some-provides"


def test_official_provider_cs() -> None:
    """Test case sensitivity of the database table."""
    with db.begin():
        oprovider = db.create(
            OfficialProvider,
            Name="some-name",
            Repo="some-repo",
            Provides="some-provides",
        )
    assert bool(oprovider.ID)

    with db.begin():
        oprovider_cs = db.create(
            OfficialProvider,
            Name="SOME-NAME",
            Repo="SOME-REPO",
            Provides="SOME-PROVIDES",
        )
    assert bool(oprovider_cs.ID)

    assert oprovider.ID != oprovider_cs.ID

    assert oprovider.Name == "some-name"
    assert oprovider.Repo == "some-repo"
    assert oprovider.Provides == "some-provides"

    assert oprovider_cs.Name == "SOME-NAME"
    assert oprovider_cs.Repo == "SOME-REPO"
    assert oprovider_cs.Provides == "SOME-PROVIDES"


def test_official_provider_null_name_raises_exception() -> None:
    with pytest.raises(IntegrityError):
        OfficialProvider(Repo="some-repo", Provides="some-provides")


def test_official_provider_null_repo_raises_exception() -> None:
    with pytest.raises(IntegrityError):
        OfficialProvider(Name="some-name", Provides="some-provides")


def test_official_provider_null_provides_raises_exception() -> None:
    with pytest.raises(IntegrityError):
        OfficialProvider(Name="some-name", Repo="some-repo")
