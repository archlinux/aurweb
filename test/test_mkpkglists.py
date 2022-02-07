import json

from typing import List, Union
from unittest import mock

import py
import pytest

from aurweb import config, db, util
from aurweb.models import License, Package, PackageBase, PackageDependency, PackageLicense, User
from aurweb.models.account_type import USER_ID
from aurweb.models.dependency_type import DEPENDS_ID
from aurweb.testing import noop


class FakeFile:
    data = str()

    def __init__(self, archive: str, modes: str) -> "FakeFile":
        self.archive = archive
        self.modes = modes

    def __enter__(self, *args, **kwargs) -> "FakeFile":
        return self

    def __exit__(self, *args, **kwargs):
        print(f"Writing {self.archive}....")
        self.close()

    def write(self, data: Union[str, bytes]) -> None:
        if isinstance(data, bytes):
            data = data.decode()
        self.data += data

    def writelines(self, dataset: List[Union[str, bytes]]) -> None:
        util.apply_all(dataset, self.write)

    def close(self) -> None:
        with open(self.archive, "w") as f:
            f.write(self.data)


class MockGzipOpen:
    def __init__(self):
        self.gzips = dict()

    def open(self, archive: str, modes: str):
        self.gzips[archive] = FakeFile(archive, modes)
        return self.gzips.get(archive)

    def get(self, key: str) -> FakeFile:
        return self.gzips.get(key)

    def __getitem__(self, key: str) -> FakeFile:
        return self.get(key)

    def __contains__(self, key: str) -> bool:
        print(self.gzips.keys())
        return key in self.gzips

    def data(self, archive: str):
        return self.get(archive).data


@pytest.fixture(autouse=True)
def setup(db_test):
    config.rehash()


@pytest.fixture
def user() -> User:
    with db.begin():
        user = db.create(User, Username="test",
                         Email="test@example.org",
                         Passwd="testPassword",
                         AccountTypeID=USER_ID)
    yield user


@pytest.fixture
def packages(user: User) -> List[Package]:
    output = []
    with db.begin():
        lic = db.create(License, Name="GPL")
        for i in range(5):
            # Create the package.
            pkgbase = db.create(PackageBase, Name=f"pkgbase_{i}",
                                Packager=user)
            pkg = db.create(Package, PackageBase=pkgbase,
                            Name=f"pkg_{i}")

            # Create some related records.
            db.create(PackageLicense, Package=pkg, License=lic)
            db.create(PackageDependency, DepTypeID=DEPENDS_ID,
                      Package=pkg, DepName=f"dep_{i}",
                      DepCondition=">=1.0")

            # Add the package to our output list.
            output.append(pkg)

    # Sort output by the package name and return it.
    yield sorted(output, key=lambda k: k.Name)


@pytest.fixture
def config_mock(tmpdir: py.path.local) -> None:
    config_get = config.get
    archivedir = config.get("mkpkglists", "archivedir")

    def mock_config(section: str, key: str) -> str:
        if section == "mkpkglists":
            if key == "archivedir":
                return str(tmpdir)
            return config_get(section, key).replace(archivedir, str(tmpdir))
        return config_get(section, key)

    with mock.patch("aurweb.config.get", side_effect=mock_config):
        config.rehash()
        yield
    config.rehash()


def test_mkpkglists(tmpdir: py.path.local, config_mock: None):
    from aurweb.scripts import mkpkglists
    mkpkglists.main()


@mock.patch("sys.argv", ["mkpkglists", "--extended"])
def test_mkpkglists_extended_empty(config_mock: None):
    from aurweb.scripts import mkpkglists
    mkpkglists.main()

    '''
    archives = config.get_section("mkpkglists")
    archives.pop("archivedir")

    for archive in archives.values():
        assert archive in gzips

    # Expect that packagesfile got created, but is empty because
    # we have no DB records.
    packages_file = archives.get("packagesfile")
    assert gzips.data(packages_file) == str()

    # Expect that pkgbasefile got created, but is empty because
    # we have no DB records.
    users_file = archives.get("pkgbasefile")
    assert gzips.data(users_file) == str()

    # Expect that userfile got created, but is empty because
    # we have no DB records.
    users_file = archives.get("userfile")
    assert gzips.data(users_file) == str()

    # Expect that packagesmetafile got created, but is empty because
    # we have no DB records; it's still a valid empty JSON list.
    meta_file = archives.get("packagesmetafile")
    assert gzips.data(meta_file) == "[\n]"

    # Expect that packagesmetafile got created, but is empty because
    # we have no DB records; it's still a valid empty JSON list.
    meta_file = archives.get("packagesmetaextfile")
    assert gzips.data(meta_file) == "[\n]"
    '''


@mock.patch("sys.argv", ["mkpkglists", "--extended"])
def test_mkpkglists_extended(config_mock: None, user: User,
                             packages: List[Package]):
    from aurweb.scripts import mkpkglists
    mkpkglists.main()

    '''
    archives = config.get_section("mkpkglists")
    archives.pop("archivedir")

    for archive in archives.values():
        assert archive in gzips

    # Expect that packagesfile got created, but is empty because
    # we have no DB records.
    packages_file = archives.get("packagesfile")
    expected = "\n".join([p.Name for p in packages]) + "\n"
    assert gzips.data(packages_file) == expected

    # Expect that pkgbasefile got created, but is empty because
    # we have no DB records.
    users_file = archives.get("pkgbasefile")
    expected = "\n".join([p.PackageBase.Name for p in packages]) + "\n"
    assert gzips.data(users_file) == expected

    # Expect that userfile got created, but is empty because
    # we have no DB records.
    users_file = archives.get("userfile")
    assert gzips.data(users_file) == "test\n"

    # Expect that packagesmetafile got created, but is empty because
    # we have no DB records; it's still a valid empty JSON list.
    meta_file = archives.get("packagesmetafile")
    data = json.loads(gzips.data(meta_file))
    assert len(data) == 5

    # Expect that packagesmetafile got created, but is empty because
    # we have no DB records; it's still a valid empty JSON list.
    meta_file = archives.get("packagesmetaextfile")
    data = json.loads(gzips.data(meta_file))
    assert len(data) == 5
    '''
