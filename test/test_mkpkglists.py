import gzip
import json
import os
from unittest import mock

import py
import pytest

from aurweb import config, db
from aurweb.models import (
    License,
    Package,
    PackageBase,
    PackageComaintainer,
    PackageDependency,
    PackageLicense,
    User,
)
from aurweb.models.account_type import USER_ID
from aurweb.models.dependency_type import DEPENDS_ID

META_KEYS = [
    "ID",
    "Name",
    "PackageBaseID",
    "PackageBase",
    "Version",
    "Description",
    "URL",
    "NumVotes",
    "Popularity",
    "OutOfDate",
    "Maintainer",
    "Submitter",
    "FirstSubmitted",
    "LastModified",
    "URLPath",
]


@pytest.fixture(autouse=True)
def setup(db_test):
    config.rehash()


@pytest.fixture
def user() -> User:
    with db.begin():
        user = db.create(
            User,
            Username="test",
            Email="test@example.org",
            Passwd="testPassword",
            AccountTypeID=USER_ID,
        )
    yield user


@pytest.fixture
def packages(user: User) -> list[Package]:
    output = []
    with db.begin():
        lic = db.create(License, Name="GPL")
        for i in range(5):
            # Create the package.
            pkgbase = db.create(
                PackageBase,
                Name=f"pkgbase_{i}",
                Packager=user,
                Submitter=user,
            )
            pkg = db.create(Package, PackageBase=pkgbase, Name=f"pkg_{i}")

            # Create some related records.
            db.create(PackageLicense, Package=pkg, License=lic)
            db.create(
                PackageDependency,
                DepTypeID=DEPENDS_ID,
                Package=pkg,
                DepName=f"dep_{i}",
                DepCondition=">=1.0",
            )
            db.create(PackageComaintainer, User=user, PackageBase=pkgbase, Priority=1)

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


def test_mkpkglists(
    tmpdir: py.path.local, config_mock: None, user: User, packages: list[Package]
):
    from aurweb.scripts import mkpkglists

    mkpkglists.main()

    PACKAGES = config.get("mkpkglists", "packagesfile")
    META = config.get("mkpkglists", "packagesmetafile")
    PKGBASE = config.get("mkpkglists", "pkgbasefile")
    USERS = config.get("mkpkglists", "userfile")

    expectations = [
        (
            PACKAGES,
            "pkg_0\npkg_1\npkg_2\npkg_3\npkg_4\n",
        ),
        (
            PKGBASE,
            "pkgbase_0\npkgbase_1\npkgbase_2\npkgbase_3\npkgbase_4\n",
        ),
        (USERS, "test\n"),
    ]

    for (file, expected_content) in expectations:
        with gzip.open(file, "r") as f:
            file_content = f.read().decode()
            assert file_content == expected_content

    with gzip.open(META) as f:
        metadata = json.load(f)

    assert len(metadata) == len(packages)
    for pkg in metadata:
        for key in META_KEYS:
            assert key in pkg, f"{pkg=} record does not have {key=}"

    for file in (PACKAGES, PKGBASE, USERS, META):
        with open(f"{file}.sha256") as f:
            file_sig_content = f.read()
            expected_prefix = f"SHA256 ({os.path.basename(file)}) = "
            assert file_sig_content.startswith(expected_prefix)
            assert len(file_sig_content) == len(expected_prefix) + 64


@mock.patch("sys.argv", ["mkpkglists", "--extended"])
def test_mkpkglists_extended_empty(config_mock: None):
    from aurweb.scripts import mkpkglists

    mkpkglists.main()

    PACKAGES = config.get("mkpkglists", "packagesfile")
    META = config.get("mkpkglists", "packagesmetafile")
    META_EXT = config.get("mkpkglists", "packagesmetaextfile")
    PKGBASE = config.get("mkpkglists", "pkgbasefile")
    USERS = config.get("mkpkglists", "userfile")

    expectations = [
        (PACKAGES, ""),
        (PKGBASE, ""),
        (USERS, ""),
        (META, "[\n]"),
        (META_EXT, "[\n]"),
    ]

    for (file, expected_content) in expectations:
        with gzip.open(file, "r") as f:
            file_content = f.read().decode()
            assert file_content == expected_content, f"{file=} contents malformed"

    for file in (PACKAGES, PKGBASE, USERS, META, META_EXT):
        with open(f"{file}.sha256") as f:
            file_sig_content = f.read()
            expected_prefix = f"SHA256 ({os.path.basename(file)}) = "
            assert file_sig_content.startswith(expected_prefix)
            assert len(file_sig_content) == len(expected_prefix) + 64


@mock.patch("sys.argv", ["mkpkglists", "--extended"])
def test_mkpkglists_extended(config_mock: None, user: User, packages: list[Package]):
    from aurweb.scripts import mkpkglists

    mkpkglists.main()

    PACKAGES = config.get("mkpkglists", "packagesfile")
    META = config.get("mkpkglists", "packagesmetafile")
    META_EXT = config.get("mkpkglists", "packagesmetaextfile")
    PKGBASE = config.get("mkpkglists", "pkgbasefile")
    USERS = config.get("mkpkglists", "userfile")

    expectations = [
        (
            PACKAGES,
            "pkg_0\npkg_1\npkg_2\npkg_3\npkg_4\n",
        ),
        (
            PKGBASE,
            "pkgbase_0\npkgbase_1\npkgbase_2\npkgbase_3\npkgbase_4\n",
        ),
        (USERS, "test\n"),
    ]

    for (file, expected_content) in expectations:
        with gzip.open(file, "r") as f:
            file_content = f.read().decode()
            assert file_content == expected_content

    with gzip.open(META) as f:
        metadata = json.load(f)

    assert len(metadata) == len(packages)
    for pkg in metadata:
        for key in META_KEYS:
            assert key in pkg, f"{pkg=} record does not have {key=}"

    with gzip.open(META_EXT) as f:
        extended_metadata = json.load(f)

    assert len(extended_metadata) == len(packages)
    for pkg in extended_metadata:
        for key in META_KEYS:
            assert key in pkg, f"{pkg=} record does not have {key=}"
        assert isinstance(pkg["Depends"], list)
        assert isinstance(pkg["License"], list)
        assert isinstance(pkg["CoMaintainers"], list)

    for file in (PACKAGES, PKGBASE, USERS, META, META_EXT):
        with open(f"{file}.sha256") as f:
            file_sig_content = f.read()
            expected_prefix = f"SHA256 ({os.path.basename(file)}) = "
            assert file_sig_content.startswith(expected_prefix)
            assert len(file_sig_content) == len(expected_prefix) + 64
