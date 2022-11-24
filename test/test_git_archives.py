from http import HTTPStatus
from typing import Tuple
from unittest import mock

import py
import pygit2
import pytest
from fastapi.testclient import TestClient

from aurweb import asgi, config, db
from aurweb.archives.spec.base import GitInfo, SpecBase
from aurweb.models import Package, PackageBase, User
from aurweb.scripts import git_archive
from aurweb.testing.requests import Request


@pytest.fixture
def mock_metadata_archive(
    tmp_path: py.path.local,
) -> Tuple[py.path.local, py.path.local]:
    metadata_path = tmp_path / "metadata.git"

    get_ = config.get

    def mock_config(section: str, option: str) -> str:
        if section == "git-archive":
            if option == "metadata-repo":
                return str(metadata_path)
        return get_(section, option)

    with mock.patch("aurweb.config.get", side_effect=mock_config):
        yield metadata_path


@pytest.fixture
def mock_users_archive(tmp_path: py.path.local) -> py.path.local:
    users_path = tmp_path / "users.git"

    get_ = config.get

    def mock_config(section: str, option: str) -> str:
        if section == "git-archive":
            if option == "users-repo":
                return str(users_path)
        return get_(section, option)

    with mock.patch("aurweb.config.get", side_effect=mock_config):
        yield users_path


@pytest.fixture
def mock_pkgbases_archive(tmp_path: py.path.local) -> py.path.local:
    pkgbases_path = tmp_path / "pkgbases.git"

    get_ = config.get

    def mock_config(section: str, option: str) -> str:
        if section == "git-archive":
            if option == "pkgbases-repo":
                return str(pkgbases_path)
        return get_(section, option)

    with mock.patch("aurweb.config.get", side_effect=mock_config):
        yield pkgbases_path


@pytest.fixture
def mock_pkgnames_archive(tmp_path: py.path.local) -> py.path.local:
    pkgnames_path = tmp_path / "pkgnames.git"

    get_ = config.get

    def mock_config(section: str, option: str) -> str:
        if section == "git-archive":
            if option == "pkgnames-repo":
                return str(pkgnames_path)
        return get_(section, option)

    with mock.patch("aurweb.config.get", side_effect=mock_config):
        yield pkgnames_path


@pytest.fixture
def metadata(mock_metadata_archive: py.path.local) -> py.path.local:
    args = [__name__, "--spec", "metadata"]
    with mock.patch("sys.argv", args):
        yield mock_metadata_archive


@pytest.fixture
def users(mock_users_archive: py.path.local) -> py.path.local:
    args = [__name__, "--spec", "users"]
    with mock.patch("sys.argv", args):
        yield mock_users_archive


@pytest.fixture
def pkgbases(mock_pkgbases_archive: py.path.local) -> py.path.local:
    args = [__name__, "--spec", "pkgbases"]
    with mock.patch("sys.argv", args):
        yield mock_pkgbases_archive


@pytest.fixture
def pkgnames(mock_pkgnames_archive: py.path.local) -> py.path.local:
    args = [__name__, "--spec", "pkgnames"]
    with mock.patch("sys.argv", args):
        yield mock_pkgnames_archive


@pytest.fixture
def client() -> TestClient:
    yield TestClient(app=asgi.app)


@pytest.fixture
def user(db_test: None) -> User:
    with db.begin():
        user_ = db.create(
            User,
            Username="test",
            Email="test@example.org",
            Passwd="testPassword",
        )

    yield user_


@pytest.fixture
def package(user: User) -> Package:
    with db.begin():
        pkgbase_ = db.create(
            PackageBase,
            Name="test",
            Maintainer=user,
            Packager=user,
        )

        pkg_ = db.create(
            Package,
            PackageBase=pkgbase_,
            Name="test",
        )

    yield pkg_


def commit_count(repo: pygit2.Repository) -> int:
    commits = 0
    for _ in repo.walk(repo.head.target):
        commits += 1
    return commits


def test_specbase_raises_notimplementederror():
    spec = SpecBase()
    with pytest.raises(NotImplementedError):
        spec.generate()


def test_gitinfo_config(tmpdir: py.path.local):
    path = tmpdir / "test.git"
    git_info = GitInfo(path, {"user.name": "Test Person"})
    git_archive.init_repository(git_info)

    repo = pygit2.Repository(path)
    assert repo.config["user.name"] == "Test Person"


def test_metadata(metadata: py.path.local, package: Package):
    # Run main(), which creates mock_metadata_archive and commits current
    # package data to it, exercising the "diff detected, committing" path
    assert git_archive.main() == 0
    repo = pygit2.Repository(metadata)
    assert commit_count(repo) == 1

    # Run main() again to exercise the "no diff detected" path
    assert git_archive.main() == 0
    repo = pygit2.Repository(metadata)
    assert commit_count(repo) == 1


def test_metadata_change(
    client: TestClient, metadata: py.path.local, user: User, package: Package
):
    """Test that metadata changes via aurweb cause git_archive to produce diffs."""
    # Run main(), which creates mock_metadata_archive and commits current
    # package data to it, exercising the "diff detected, committing" path
    assert git_archive.main() == 0
    repo = pygit2.Repository(metadata)
    assert commit_count(repo) == 1

    # Now, we modify `package`-related metadata via aurweb POST.
    pkgbasename = package.PackageBase.Name
    cookies = {"AURSID": user.login(Request(), "testPassword")}

    with client as request:
        endp = f"/pkgbase/{pkgbasename}/keywords"
        post_data = {"keywords": "abc def"}
        request.cookies = cookies
        resp = request.post(endp, data=post_data)
    assert resp.status_code == HTTPStatus.OK

    # Run main() again, which should now produce a new commit with the
    # keyword changes we just made
    assert git_archive.main() == 0
    repo = pygit2.Repository(metadata)
    assert commit_count(repo) == 2


def test_metadata_delete(client: TestClient, metadata: py.path.local, package: Package):
    # Run main(), which creates mock_metadata_archive and commits current
    # package data to it, exercising the "diff detected, committing" path
    assert git_archive.main() == 0
    repo = pygit2.Repository(metadata)
    assert commit_count(repo) == 1

    with db.begin():
        db.delete(package)

    # The deletion here should have caused a diff to be produced in git
    assert git_archive.main() == 0
    repo = pygit2.Repository(metadata)
    assert commit_count(repo) == 2


def test_users(users: py.path.local, user: User):
    assert git_archive.main() == 0
    repo = pygit2.Repository(users)
    assert commit_count(repo) == 1


def test_pkgbases(pkgbases: py.path.local, package: Package):
    assert git_archive.main() == 0
    repo = pygit2.Repository(pkgbases)
    assert commit_count(repo) == 1


def test_pkgnames(pkgnames: py.path.local, package: Package):
    assert git_archive.main() == 0
    repo = pygit2.Repository(pkgnames)
    assert commit_count(repo) == 1
