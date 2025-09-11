import tempfile
from typing import Generator
from unittest import mock

import py
import pytest

from aurweb import config, db
from aurweb.models import OfficialProvider
from aurweb.scripts import aurblup
from aurweb.testing.alpm import AlpmDatabase


@pytest.fixture
def tempdir() -> Generator[str]:
    with tempfile.TemporaryDirectory() as name:
        yield name


@pytest.fixture
def alpm_db(tempdir: py.path.local) -> Generator[AlpmDatabase]:
    yield AlpmDatabase(tempdir)


@pytest.fixture(autouse=True)
def setup(db_test, alpm_db: AlpmDatabase, tempdir: py.path.local) -> Generator[None]:
    config_get = config.get

    def mock_config_get(section: str, key: str) -> str:
        value = config_get(section, key)
        if section == "aurblup":
            if key == "db-path":
                return alpm_db.local
            elif key == "server":
                return f"file://{alpm_db.remote}"
            elif key == "sync-dbs":
                return alpm_db.repo
        return value

    with mock.patch("aurweb.config.get", side_effect=mock_config_get):
        config.rehash()
        yield
    config.rehash()


def test_aurblup(alpm_db: AlpmDatabase):
    # Test that we can add a package.
    alpm_db.add("pkg", "1.0", "x86_64", provides=["pkg2", "pkg3"])
    alpm_db.add("pkg2", "2.0", "x86_64")
    aurblup.main()

    # Test that the package got added to the database.
    for name in ("pkg", "pkg2"):
        pkg = db.query(OfficialProvider).filter(OfficialProvider.Name == name).first()
        assert pkg is not None

    # Test that we can remove the package.
    alpm_db.remove("pkg")

    # Run aurblup again with forced repository update.
    aurblup.main(True)

    # Expect that the database got updated accordingly.
    pkg = db.query(OfficialProvider).filter(OfficialProvider.Name == "pkg").first()
    assert pkg is None
    pkg2 = db.query(OfficialProvider).filter(OfficialProvider.Name == "pkg2").first()
    assert pkg2 is not None


def test_aurblup_cleanup(alpm_db: AlpmDatabase):
    # Add a package and sync up the database.
    alpm_db.add("pkg", "1.0", "x86_64", provides=["pkg2", "pkg3"])
    aurblup.main()

    # Now, let's insert an OfficialPackage that doesn't exist,
    # then exercise the old provider deletion path.
    with db.begin():
        db.create(
            OfficialProvider, Name="fake package", Repo="test", Provides="package"
        )

    # Run aurblup again.
    aurblup.main()

    # Expect that the fake package got deleted because it's
    # not in alpm_db anymore.
    providers = (
        db.query(OfficialProvider).filter(OfficialProvider.Name == "fake package").all()
    )
    assert len(providers) == 0


def test_aurblup_repo_change(alpm_db: AlpmDatabase):
    # Add a package and sync up the database.
    alpm_db.add("pkg", "1.0", "x86_64", provides=["pkg2", "pkg3"])
    aurblup.main()

    # We should find an entry with repo "test"
    op = db.query(OfficialProvider).filter(OfficialProvider.Name == "pkg").first()
    assert op.Repo == "test"

    # Modify the repo to something that does not exist.
    op.Repo = "nonsense"

    # Run our script.
    aurblup.main()

    # Repo should be set back to "test"
    db.refresh(op)
    assert op.Repo == "test"
