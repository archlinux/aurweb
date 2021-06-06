import pytest

from sqlalchemy.exc import IntegrityError

from aurweb.db import create
from aurweb.models.official_provider import OfficialProvider
from aurweb.testing import setup_test_db


@pytest.fixture(autouse=True)
def setup():
    setup_test_db("OfficialProviders")


def test_official_provider_creation():
    oprovider = create(OfficialProvider,
                       Name="some-name",
                       Repo="some-repo",
                       Provides="some-provides")
    assert bool(oprovider.ID)
    assert oprovider.Name == "some-name"
    assert oprovider.Repo == "some-repo"
    assert oprovider.Provides == "some-provides"


def test_official_provider_cs():
    """ Test case sensitivity of the database table. """
    oprovider = create(OfficialProvider,
                       Name="some-name",
                       Repo="some-repo",
                       Provides="some-provides")
    assert bool(oprovider.ID)

    oprovider_cs = create(OfficialProvider,
                          Name="SOME-NAME",
                          Repo="SOME-REPO",
                          Provides="SOME-PROVIDES")
    assert bool(oprovider_cs.ID)

    assert oprovider.ID != oprovider_cs.ID

    assert oprovider.Name == "some-name"
    assert oprovider.Repo == "some-repo"
    assert oprovider.Provides == "some-provides"

    assert oprovider_cs.Name == "SOME-NAME"
    assert oprovider_cs.Repo == "SOME-REPO"
    assert oprovider_cs.Provides == "SOME-PROVIDES"


def test_official_provider_null_name_raises_exception():
    from aurweb.db import session
    with pytest.raises(IntegrityError):
        create(OfficialProvider,
               Repo="some-repo",
               Provides="some-provides")
    session.rollback()


def test_official_provider_null_repo_raises_exception():
    from aurweb.db import session
    with pytest.raises(IntegrityError):
        create(OfficialProvider,
               Name="some-name",
               Provides="some-provides")
    session.rollback()


def test_official_provider_null_provides_raises_exception():
    from aurweb.db import session
    with pytest.raises(IntegrityError):
        create(OfficialProvider,
               Name="some-name",
               Repo="some-repo")
    session.rollback()
