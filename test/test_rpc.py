import re
from http import HTTPStatus
from typing import Generator
from unittest import mock

import orjson
import pytest
from fastapi.testclient import TestClient
from redis.client import Pipeline

import aurweb.models.dependency_type as dt
import aurweb.models.relation_type as rt
from aurweb import asgi, config, db, rpc, scripts, time
from aurweb.aur_redis import redis_connection
from aurweb.models.account_type import USER_ID
from aurweb.models.dependency_type import DEPENDS_ID
from aurweb.models.group import Group
from aurweb.models.license import License
from aurweb.models.package import Package
from aurweb.models.package_base import PackageBase
from aurweb.models.package_comaintainer import PackageComaintainer
from aurweb.models.package_dependency import PackageDependency
from aurweb.models.package_group import PackageGroup
from aurweb.models.package_keyword import PackageKeyword
from aurweb.models.package_license import PackageLicense
from aurweb.models.package_relation import PackageRelation
from aurweb.models.package_vote import PackageVote
from aurweb.models.relation_type import PROVIDES_ID
from aurweb.models.user import User


@pytest.fixture
def client() -> TestClient:
    yield TestClient(app=asgi.app)


@pytest.fixture
def user(db_test) -> Generator[User]:
    with db.begin():
        user = db.create(
            User,
            Username="test",
            Email="test@example.org",
            RealName="Test User 1",
            Passwd=str(),
            AccountTypeID=USER_ID,
        )
    yield user


@pytest.fixture
def user2() -> Generator[User]:
    with db.begin():
        user = db.create(
            User,
            Username="user2",
            Email="user2@example.org",
            RealName="Test User 2",
            Passwd=str(),
            AccountTypeID=USER_ID,
        )
    yield user


@pytest.fixture
def user3() -> Generator[User]:
    with db.begin():
        user = db.create(
            User,
            Username="user3",
            Email="user3@example.org",
            RealName="Test User 3",
            Passwd=str(),
            AccountTypeID=USER_ID,
        )
    yield user


@pytest.fixture
def packages(user: User, user2: User, user3: User) -> Generator[list[Package]]:
    output = []

    # Create package records used in our tests.
    with db.begin():
        pkgbase = db.create(
            PackageBase,
            Name="big-chungus",
            Maintainer=user,
            Packager=user,
            Submitter=user2,
        )
        pkg = db.create(
            Package,
            PackageBase=pkgbase,
            Name=pkgbase.Name,
            Description="Bunny bunny around bunny",
            URL="https://example.com/",
        )
        output.append(pkg)

        pkgbase = db.create(
            PackageBase,
            Name="chungy-chungus",
            Maintainer=user,
            Packager=user,
            Submitter=user2,
        )
        pkg = db.create(
            Package,
            PackageBase=pkgbase,
            Name=pkgbase.Name,
            Description="Wubby wubby on wobba wuubu",
            URL="https://example.com/",
        )
        output.append(pkg)

        pkgbase = db.create(
            PackageBase, Name="gluggly-chungus", Maintainer=user, Packager=user
        )
        pkg = db.create(
            Package,
            PackageBase=pkgbase,
            Name=pkgbase.Name,
            Description="glurrba glurrba gur globba",
            URL="https://example.com/",
        )
        output.append(pkg)

        pkgbase = db.create(
            PackageBase, Name="fugly-chungus", Maintainer=user, Packager=user
        )

        desc = "A Package belonging to a PackageBase with another name."
        pkg = db.create(
            Package,
            PackageBase=pkgbase,
            Name="other-pkg",
            Description=desc,
            URL="https://example.com",
        )
        output.append(pkg)

        pkgbase = db.create(PackageBase, Name="woogly-chungus")
        pkg = db.create(
            Package,
            PackageBase=pkgbase,
            Name=pkgbase.Name,
            Description="wuggla woblabeloop shemashmoop",
            URL="https://example.com/",
        )
        output.append(pkg)

    # Setup a few more related records on the first package:
    # a license, group, some keywords, comaintainer and some votes.
    with db.begin():
        lic = db.create(License, Name="GPL")
        db.create(PackageLicense, Package=output[0], License=lic)

        grp = db.create(Group, Name="testgroup")
        db.create(PackageGroup, Package=output[0], Group=grp)

        db.create(
            PackageComaintainer,
            PackageBase=output[0].PackageBase,
            User=user2,
            Priority=1,
        )

        for keyword in ["big-chungus", "smol-chungus", "sizeable-chungus"]:
            db.create(
                PackageKeyword, PackageBase=output[0].PackageBase, Keyword=keyword
            )

        now = time.utcnow()
        for user_ in [user, user2, user3]:
            db.create(
                PackageVote, User=user_, PackageBase=output[0].PackageBase, VoteTS=now
            )
    scripts.popupdate.run_single(output[0].PackageBase)

    yield output


@pytest.fixture
def depends(packages: list[Package]) -> Generator[list[PackageDependency]]:
    output = []

    with db.begin():
        dep = db.create(
            PackageDependency,
            Package=packages[0],
            DepTypeID=dt.DEPENDS_ID,
            DepName="chungus-depends",
        )
        output.append(dep)

        dep = db.create(
            PackageDependency,
            Package=packages[1],
            DepTypeID=dt.DEPENDS_ID,
            DepName="chungy-depends",
        )
        output.append(dep)

        dep = db.create(
            PackageDependency,
            Package=packages[0],
            DepTypeID=dt.OPTDEPENDS_ID,
            DepName="chungus-optdepends",
            DepCondition="=50",
        )
        output.append(dep)

        dep = db.create(
            PackageDependency,
            Package=packages[0],
            DepTypeID=dt.MAKEDEPENDS_ID,
            DepName="chungus-makedepends",
        )
        output.append(dep)

        dep = db.create(
            PackageDependency,
            Package=packages[0],
            DepTypeID=dt.CHECKDEPENDS_ID,
            DepName="chungus-checkdepends",
        )
        output.append(dep)

    yield output


@pytest.fixture
def relations(user: User, packages: list[Package]) -> Generator[list[PackageRelation]]:
    output = []

    with db.begin():
        rel = db.create(
            PackageRelation,
            Package=packages[0],
            RelTypeID=rt.CONFLICTS_ID,
            RelName="chungus-conflicts",
        )
        output.append(rel)

        rel = db.create(
            PackageRelation,
            Package=packages[1],
            RelTypeID=rt.CONFLICTS_ID,
            RelName="chungy-conflicts",
        )
        output.append(rel)

        rel = db.create(
            PackageRelation,
            Package=packages[0],
            RelTypeID=rt.PROVIDES_ID,
            RelName="chungus-provides",
            RelCondition="<=200",
        )
        output.append(rel)

        rel = db.create(
            PackageRelation,
            Package=packages[0],
            RelTypeID=rt.REPLACES_ID,
            RelName="chungus-replaces",
            RelCondition="<=200",
        )
        output.append(rel)

    # Finally, yield the packages.
    yield output


@pytest.fixture
def comaintainer(
    user2: User, user3: User, packages: list[Package]
) -> Generator[list[PackageComaintainer]]:
    output = []

    with db.begin():
        comaintainer = db.create(
            PackageComaintainer,
            User=user2,
            PackageBase=packages[0].PackageBase,
            Priority=1,
        )
        output.append(comaintainer)

        comaintainer = db.create(
            PackageComaintainer,
            User=user3,
            PackageBase=packages[0].PackageBase,
            Priority=1,
        )
        output.append(comaintainer)

    # Finally, yield the packages.
    yield output


@pytest.fixture(autouse=True)
def setup(db_test):
    # Create some extra package relationships.
    pass


@pytest.fixture
def pipeline():
    redis = redis_connection()
    pipeline = redis.pipeline()

    # 'testclient' is our fallback value in case request.client is None
    # which is the case for TestClient
    pipeline.delete("ratelimit-ws:testclient")
    pipeline.delete("ratelimit:testclient")
    pipeline.execute()

    yield pipeline


def test_rpc_documentation(client: TestClient):
    with client as request:
        resp = request.get("/rpc")
    assert resp.status_code == int(HTTPStatus.OK)
    assert "aurweb RPC Interface" in resp.text


def test_rpc_documentation_missing():
    config_get = config.get

    def mock_get(section: str, key: str) -> str:
        if section == "options" and key == "aurwebdir":
            return "/missing"
        return config_get(section, key)

    with mock.patch("aurweb.config.get", side_effect=mock_get):
        config.rehash()
        expr = r"^doc/rpc\.html could not be read$"
        with pytest.raises(OSError, match=expr):
            rpc.documentation()
    config.rehash()


def test_rpc_singular_info(
    client: TestClient,
    user: User,
    user2: User,
    packages: list[Package],
    depends: list[PackageDependency],
    relations: list[PackageRelation],
    comaintainer: list[PackageComaintainer],
):
    # Define expected response.
    pkg = packages[0]
    expected_data = {
        "version": 5,
        "results": [
            {
                "Name": pkg.Name,
                "Version": pkg.Version,
                "Description": pkg.Description,
                "URL": pkg.URL,
                "PackageBase": pkg.PackageBase.Name,
                "NumVotes": pkg.PackageBase.NumVotes,
                "Popularity": float(pkg.PackageBase.Popularity),
                "OutOfDate": None,
                "Maintainer": user.Username,
                "Submitter": user2.Username,
                "URLPath": f"/cgit/aur.git/snapshot/{pkg.Name}.tar.gz",
                "Depends": ["chungus-depends"],
                "OptDepends": ["chungus-optdepends=50"],
                "MakeDepends": ["chungus-makedepends"],
                "CheckDepends": ["chungus-checkdepends"],
                "Conflicts": ["chungus-conflicts"],
                "CoMaintainers": ["user2", "user3"],
                "Provides": ["chungus-provides<=200"],
                "Replaces": ["chungus-replaces<=200"],
                "License": [pkg.package_licenses.first().License.Name],
                "Keywords": ["big-chungus", "sizeable-chungus", "smol-chungus"],
                "Groups": ["testgroup"],
            }
        ],
        "resultcount": 1,
        "type": "multiinfo",
    }

    # Make dummy request.
    with client as request:
        resp = request.get(
            "/rpc",
            params={
                "v": 5,
                "type": "info",
                "arg": ["chungy-chungus", "big-chungus"],
            },
        )

    # Load  request response into Python dictionary.
    response_data = orjson.loads(resp.text)

    # Remove the FirstSubmitted LastModified, ID and PackageBaseID keys from
    # reponse, as the key's values aren't guaranteed to match between the two
    # (the keys are already removed from 'expected_data').
    for i in ["FirstSubmitted", "LastModified", "ID", "PackageBaseID"]:
        response_data["results"][0].pop(i)

    # Validate that the new dictionaries are the same.
    assert response_data == expected_data


def test_rpc_split_package_urlpath(client: TestClient, user: User):
    with db.begin():
        pkgbase = db.create(PackageBase, Name="pkg", Maintainer=user, Packager=user)
        pkgs = [
            db.create(Package, PackageBase=pkgbase, Name="pkg_1"),
            db.create(Package, PackageBase=pkgbase, Name="pkg_2"),
        ]

    with client as request:
        response = request.get(
            "/rpc",
            params={
                "v": 5,
                "type": "info",
                "arg": [pkgs[0].Name],
            },
        )

    data = orjson.loads(response.text)
    snapshot_uri = config.get("options", "snapshot_uri")
    urlpath = data.get("results")[0].get("URLPath")
    assert urlpath == (snapshot_uri % pkgbase.Name)


def test_rpc_nonexistent_package(client: TestClient):
    # Make dummy request.
    with client as request:
        response = request.get("/rpc/?v=5&type=info&arg=nonexistent-package")

    # Load request response into Python dictionary.
    response_data = orjson.loads(response.content.decode())

    # Validate data.
    assert response_data["resultcount"] == 0


def test_rpc_multiinfo(client: TestClient, packages: list[Package]):
    # Make dummy request.
    request_packages = ["big-chungus", "chungy-chungus"]
    with client as request:
        response = request.get(
            "/rpc", params={"v": 5, "type": "info", "arg[]": request_packages}
        )

    # Load request response into Python dictionary.
    response_data = orjson.loads(response.content.decode())

    # Validate data.
    for i in response_data["results"]:
        request_packages.remove(i["Name"])

    assert request_packages == []


def test_rpc_mixedargs(client: TestClient, packages: list[Package]):
    # Make dummy request.
    response1_packages = ["gluggly-chungus"]
    response2_packages = ["gluggly-chungus", "chungy-chungus"]

    with client as request:
        # Supply all of the args in the url to enforce ordering.
        response1 = request.get(
            "/rpc?v=5&arg[]=big-chungus&arg=gluggly-chungus&type=info"
        )
    assert response1.status_code == int(HTTPStatus.OK)

    with client as request:
        response2 = request.get(
            "/rpc?v=5&arg=big-chungus&arg[]=gluggly-chungus"
            "&type=info&arg[]=chungy-chungus"
        )
    assert response1.status_code == int(HTTPStatus.OK)

    # Load request response into Python dictionary.
    response1_data = orjson.loads(response1.content.decode())
    response2_data = orjson.loads(response2.content.decode())

    # Validate data.
    for i in response1_data["results"]:
        response1_packages.remove(i["Name"])

    for i in response2_data["results"]:
        response2_packages.remove(i["Name"])

    for i in [response1_packages, response2_packages]:
        assert i == []


def test_rpc_no_dependencies_omits_key(
    client: TestClient,
    user: User,
    user2: User,
    packages: list[Package],
    depends: list[PackageDependency],
    relations: list[PackageRelation],
):
    """
    This makes sure things like 'MakeDepends' get removed from JSON strings
    when they don't have set values.
    """
    pkg = packages[1]
    expected_response = {
        "version": 5,
        "results": [
            {
                "Name": pkg.Name,
                "Version": pkg.Version,
                "Description": pkg.Description,
                "URL": pkg.URL,
                "PackageBase": pkg.PackageBase.Name,
                "NumVotes": pkg.PackageBase.NumVotes,
                "Popularity": int(pkg.PackageBase.Popularity),
                "OutOfDate": None,
                "Maintainer": user.Username,
                "Submitter": user2.Username,
                "URLPath": "/cgit/aur.git/snapshot/chungy-chungus.tar.gz",
                "Depends": ["chungy-depends"],
                "Conflicts": ["chungy-conflicts"],
                "License": [],
                "Keywords": [],
            }
        ],
        "resultcount": 1,
        "type": "multiinfo",
    }

    # Make dummy request.
    with client as request:
        response = request.get(
            "/rpc", params={"v": 5, "type": "info", "arg": "chungy-chungus"}
        )
    response_data = orjson.loads(response.content.decode())

    # Remove inconsistent keys.
    for i in ["ID", "PackageBaseID", "FirstSubmitted", "LastModified"]:
        response_data["results"][0].pop(i)

    assert response_data == expected_response


def test_rpc_bad_type(client: TestClient):
    # Define expected response.
    expected_data = {
        "version": 5,
        "results": [],
        "resultcount": 0,
        "type": "error",
        "error": "Incorrect request type specified.",
    }

    # Make dummy request.
    with client as request:
        response = request.get(
            "/rpc", params={"v": 5, "type": "invalid-type", "arg": "big-chungus"}
        )

    # Load  request response into Python dictionary.
    response_data = orjson.loads(response.content.decode())

    # Validate data.
    assert expected_data == response_data


def test_rpc_bad_version(client: TestClient):
    # Define expected response.
    expected_data = {
        "version": 0,
        "resultcount": 0,
        "results": [],
        "type": "error",
        "error": "Invalid version specified.",
    }

    # Make dummy request.
    with client as request:
        response = request.get(
            "/rpc", params={"v": 0, "type": "info", "arg": "big-chungus"}
        )

    # Load  request response into Python dictionary.
    response_data = orjson.loads(response.content.decode())

    # Validate data.
    assert expected_data == response_data


def test_rpc_no_version(client: TestClient):
    # Define expected response.
    expected_data = {
        "version": None,
        "resultcount": 0,
        "results": [],
        "type": "error",
        "error": "Please specify an API version.",
    }

    # Make dummy request.
    with client as request:
        response = request.get("/rpc", params={"type": "info", "arg": "big-chungus"})

    # Load  request response into Python dictionary.
    response_data = orjson.loads(response.content.decode())

    # Validate data.
    assert expected_data == response_data


def test_rpc_no_type(client: TestClient):
    # Define expected response.
    expected_data = {
        "version": 5,
        "results": [],
        "resultcount": 0,
        "type": "error",
        "error": "No request type/data specified.",
    }

    # Make dummy request.
    with client as request:
        response = request.get("/rpc", params={"v": 5, "arg": "big-chungus"})

    # Load  request response into Python dictionary.
    response_data = orjson.loads(response.content.decode())

    # Validate data.
    assert expected_data == response_data


def test_rpc_no_args(client: TestClient):
    # Define expected response.
    expected_data = {
        "version": 5,
        "results": [],
        "resultcount": 0,
        "type": "error",
        "error": "No request type/data specified.",
    }

    # Make dummy request.
    with client as request:
        response = request.get("/rpc", params={"v": 5, "type": "info"})

    # Load  request response into Python dictionary.
    response_data = orjson.loads(response.content.decode())

    # Validate data.
    assert expected_data == response_data


def test_rpc_no_maintainer(client: TestClient, packages: list[Package]):
    # Make dummy request.
    with client as request:
        response = request.get(
            "/rpc", params={"v": 5, "type": "info", "arg": "woogly-chungus"}
        )

    # Load  request response into Python dictionary.
    response_data = orjson.loads(response.content.decode())

    # Validate data.
    assert response_data["results"][0]["Maintainer"] is None


def test_rpc_suggest_pkgbase(client: TestClient, packages: list[Package]):
    params = {"v": 5, "type": "suggest-pkgbase", "arg": "big"}
    with client as request:
        response = request.get("/rpc", params=params)
    data = response.json()
    assert data == ["big-chungus"]

    params["arg"] = "chungy"
    with client as request:
        response = request.get("/rpc", params=params)
    data = response.json()
    assert data == ["chungy-chungus"]

    # Test no arg supplied.
    del params["arg"]
    with client as request:
        response = request.get("/rpc", params=params)
    data = response.json()
    assert data == []

    # Test that suggestions are only given based on the beginning
    # of the keyword string.
    params["arg"] = "ther-pkg"
    with client as request:
        response = request.get("/rpc", params=params)
    data = response.json()
    assert data == []


def test_rpc_suggest(client: TestClient, packages: list[Package]):
    params = {"v": 5, "type": "suggest", "arg": "other"}
    with client as request:
        response = request.get("/rpc", params=params)
    data = response.json()
    assert data == ["other-pkg"]

    # Test non-existent Package.
    params["arg"] = "nonexistent"
    with client as request:
        response = request.get("/rpc", params=params)
    data = response.json()
    assert data == []

    # Test no arg supplied.
    del params["arg"]
    with client as request:
        response = request.get("/rpc", params=params)
    data = response.json()
    assert data == []

    # Test that suggestions are only given based on the beginning
    # of the keyword string.
    params["arg"] = "ther-pkg"
    with client as request:
        response = request.get("/rpc", params=params)
    data = response.json()
    assert data == []


def mock_config_getint(section: str, key: str):
    if key == "request_limit":
        return 4
    elif key == "window_length":
        return 100
    return config.getint(section, key)


@mock.patch("aurweb.config.getint", side_effect=mock_config_getint)
def test_rpc_ratelimit(
    getint: mock.MagicMock,
    client: TestClient,
    pipeline: Pipeline,
    packages: list[Package],
):
    params = {"v": 5, "type": "suggest-pkgbase", "arg": "big"}

    for i in range(4):
        # The first 4 requests should be good.
        with client as request:
            response = request.get("/rpc", params=params)
        assert response.status_code == int(HTTPStatus.OK)

    # The fifth request should be banned.
    with client as request:
        response = request.get("/rpc", params=params)
    assert response.status_code == int(HTTPStatus.TOO_MANY_REQUESTS)

    # Delete the cached records.
    pipeline.delete("ratelimit-ws:testclient")
    pipeline.delete("ratelimit:testclient")
    one, two = pipeline.execute()
    assert one and two

    # The new first request should be good.
    with client as request:
        response = request.get("/rpc", params=params)
    assert response.status_code == int(HTTPStatus.OK)


def test_rpc_etag(client: TestClient, packages: list[Package]):
    params = {"v": 5, "type": "suggest-pkgbase", "arg": "big"}

    with client as request:
        response1 = request.get("/rpc", params=params)
    with client as request:
        response2 = request.get("/rpc", params=params)

    assert response1.headers.get("ETag") is not None
    assert response1.headers.get("ETag") != str()
    assert response1.headers.get("ETag") == response2.headers.get("ETag")


def test_rpc_search_arg_too_small(client: TestClient):
    params = {"v": 5, "type": "search", "arg": "b"}
    with client as request:
        response = request.get("/rpc", params=params)
    assert response.status_code == int(HTTPStatus.OK)
    assert response.json().get("error") == "Query arg too small."


def test_rpc_search(client: TestClient, packages: list[Package]):
    params = {"v": 5, "type": "search", "arg": "big"}
    with client as request:
        response = request.get("/rpc", params=params)
    assert response.status_code == int(HTTPStatus.OK)

    data = response.json()
    assert data.get("resultcount") == 1

    result = data.get("results")[0]
    assert result.get("Name") == packages[0].Name
    assert result.get("Submitter") is None

    # Test the If-None-Match headers.
    etag = response.headers.get("ETag").strip('"')
    headers = {"If-None-Match": etag}
    response = request.get("/rpc", params=params, headers=headers)
    assert response.status_code == int(HTTPStatus.NOT_MODIFIED)
    assert response.content == b""

    # No args on non-m by types return an error.
    del params["arg"]
    with client as request:
        response = request.get("/rpc", params=params)
    assert response.json().get("error") == "No request type/data specified."


def test_rpc_msearch(client: TestClient, user: User, packages: list[Package]):
    params = {"v": 5, "type": "msearch", "arg": user.Username}
    with client as request:
        response = request.get("/rpc", params=params)
    data = response.json()

    # user1 maintains 4 packages; assert that we got them all.
    assert data.get("resultcount") == 4
    names = list(sorted(r.get("Name") for r in data.get("results")))
    expected_results = ["big-chungus", "chungy-chungus", "gluggly-chungus", "other-pkg"]
    assert names == expected_results

    # Search for a non-existent maintainer, giving us zero packages.
    params["arg"] = "blah-blah"
    response = request.get("/rpc", params=params)
    data = response.json()
    assert data.get("resultcount") == 0

    with db.begin():
        packages[0].PackageBase.Maintainer = None

    # A missing arg still succeeds, but it returns all orphans.
    # Just verify that we receive no error and the orphaned result.
    params.pop("arg")
    response = request.get("/rpc", params=params)
    data = response.json()
    assert data.get("resultcount") == 2
    result = data.get("results")[0]
    assert result.get("Name") == "big-chungus"


def test_rpc_search_depends(
    client: TestClient, packages: list[Package], depends: list[PackageDependency]
):
    params = {"v": 5, "type": "search", "by": "depends", "arg": "chungus-depends"}
    with client as request:
        response = request.get("/rpc", params=params)
    data = response.json()
    assert data.get("resultcount") == 1
    result = data.get("results")[0]
    assert result.get("Name") == packages[0].Name


def test_rpc_search_makedepends(
    client: TestClient, packages: list[Package], depends: list[PackageDependency]
):
    params = {
        "v": 5,
        "type": "search",
        "by": "makedepends",
        "arg": "chungus-makedepends",
    }
    with client as request:
        response = request.get("/rpc", params=params)
    data = response.json()
    assert data.get("resultcount") == 1
    result = data.get("results")[0]
    assert result.get("Name") == packages[0].Name


def test_rpc_search_optdepends(
    client: TestClient, packages: list[Package], depends: list[PackageDependency]
):
    params = {"v": 5, "type": "search", "by": "optdepends", "arg": "chungus-optdepends"}
    with client as request:
        response = request.get("/rpc", params=params)
    data = response.json()
    assert data.get("resultcount") == 1
    result = data.get("results")[0]
    assert result.get("Name") == packages[0].Name


def test_rpc_search_checkdepends(
    client: TestClient, packages: list[Package], depends: list[PackageDependency]
):
    params = {
        "v": 5,
        "type": "search",
        "by": "checkdepends",
        "arg": "chungus-checkdepends",
    }
    with client as request:
        response = request.get("/rpc", params=params)
    data = response.json()
    assert data.get("resultcount") == 1
    result = data.get("results")[0]
    assert result.get("Name") == packages[0].Name


def test_rpc_search_provides(
    client: TestClient, packages: list[Package], relations: list[PackageRelation]
):
    params = {"v": 5, "type": "search", "by": "provides", "arg": "chungus-provides"}
    with client as request:
        response = request.get("/rpc", params=params)
    data = response.json()
    assert data.get("resultcount") == 1
    result = data.get("results")[0]
    assert result.get("Name") == packages[0].Name


def test_rpc_search_provides_self(
    client: TestClient, packages: list[Package], relations: list[PackageRelation]
):
    params = {"v": 5, "type": "search", "by": "provides", "arg": "big-chungus"}
    with client as request:
        response = request.get("/rpc", params=params)
    data = response.json()
    # expected to return "big-chungus"
    assert data.get("resultcount") == 1
    result = data.get("results")[0]
    assert result.get("Name") == packages[0].Name


def test_rpc_search_conflicts(
    client: TestClient, packages: list[Package], relations: list[PackageRelation]
):
    params = {"v": 5, "type": "search", "by": "conflicts", "arg": "chungus-conflicts"}
    with client as request:
        response = request.get("/rpc", params=params)
    data = response.json()
    assert data.get("resultcount") == 1
    result = data.get("results")[0]
    assert result.get("Name") == packages[0].Name


def test_rpc_search_replaces(
    client: TestClient, packages: list[Package], relations: list[PackageRelation]
):
    params = {"v": 5, "type": "search", "by": "replaces", "arg": "chungus-replaces"}
    with client as request:
        response = request.get("/rpc", params=params)
    data = response.json()
    assert data.get("resultcount") == 1
    result = data.get("results")[0]
    assert result.get("Name") == packages[0].Name


def test_rpc_search_groups(
    client: TestClient, packages: list[Package], depends: list[PackageDependency]
):
    params = {
        "v": 5,
        "type": "search",
        "by": "groups",
        "arg": "testgroup",
    }
    with client as request:
        response = request.get("/rpc", params=params)
    data = response.json()
    assert data.get("resultcount") == 1
    result = data.get("results")[0]
    assert result.get("Name") == packages[0].Name


def test_rpc_search_submitter(client: TestClient, user2: User, packages: list[Package]):
    params = {"v": 5, "type": "search", "by": "submitter", "arg": user2.Username}
    with client as request:
        response = request.get("/rpc", params=params)
    data = response.json()

    # user2 submitted 2 packages
    assert data.get("resultcount") == 2
    names = list(sorted(r.get("Name") for r in data.get("results")))
    expected_results = ["big-chungus", "chungy-chungus"]
    assert names == expected_results

    # Search for a non-existent submitter, giving us zero packages.
    params["arg"] = "blah-blah"
    response = request.get("/rpc", params=params)
    data = response.json()
    assert data.get("resultcount") == 0


def test_rpc_search_keywords(client: TestClient, packages: list[Package]):
    params = {"v": 5, "type": "search", "by": "keywords", "arg": "big-chungus"}
    with client as request:
        response = request.get("/rpc", params=params)
    data = response.json()

    # should get 2 packages
    assert data.get("resultcount") == 1
    names = list(sorted(r.get("Name") for r in data.get("results")))
    expected_results = ["big-chungus"]
    assert names == expected_results

    # non-existent search
    params["arg"] = "blah-blah"
    response = request.get("/rpc", params=params)
    data = response.json()
    assert data.get("resultcount") == 0


def test_rpc_search_comaintainers(
    client: TestClient, user2: User, packages: list[Package]
):
    params = {"v": 5, "type": "search", "by": "comaintainers", "arg": user2.Username}
    with client as request:
        response = request.get("/rpc", params=params)
    data = response.json()

    # should get 1 package
    assert data.get("resultcount") == 1
    names = list(sorted(r.get("Name") for r in data.get("results")))
    expected_results = ["big-chungus"]
    assert names == expected_results

    # non-existent search
    params["arg"] = "blah-blah"
    response = request.get("/rpc", params=params)
    data = response.json()
    assert data.get("resultcount") == 0


def test_rpc_incorrect_by(client: TestClient):
    params = {"v": 5, "type": "search", "by": "fake", "arg": "big"}
    with client as request:
        response = request.get("/rpc", params=params)
    assert response.json().get("error") == "Incorrect by field specified."


def test_rpc_jsonp_callback(client: TestClient):
    """Test the callback parameter.

    For end-to-end verification, the `examples/jsonp.html` file can be
    used to submit jsonp callback requests to the RPC.
    """
    params = {"v": 5, "type": "search", "arg": "big", "callback": "jsonCallback"}
    with client as request:
        response = request.get("/rpc", params=params)
    assert response.headers.get("content-type") == "text/javascript"
    assert re.search(r"^/\*\*/jsonCallback\(.*\)$", response.text) is not None

    # Test an invalid callback name; we get an application/json error.
    params["callback"] = "jsonCallback!"
    with client as request:
        response = request.get("/rpc", params=params)
    assert response.headers.get("content-type") == "application/json"
    assert response.json().get("error") == "Invalid callback name."


def test_rpc_post(client: TestClient, packages: list[Package]):
    data = {"v": 5, "type": "info", "arg": "big-chungus", "arg[]": ["chungy-chungus"]}
    with client as request:
        resp = request.post("/rpc", data=data)
    assert resp.status_code == int(HTTPStatus.OK)
    assert resp.json().get("resultcount") == 2


def test_rpc_too_many_search_results(client: TestClient, packages: list[Package]):
    config_getint = config.getint

    def mock_config(section: str, key: str):
        if key == "max_rpc_results":
            return 1
        return config_getint(section, key)

    params = {"v": 5, "type": "search", "arg": "chungus"}
    with mock.patch("aurweb.config.getint", side_effect=mock_config):
        with client as request:
            resp = request.get("/rpc", params=params)
    assert resp.json().get("error") == "Too many package results."


def test_rpc_too_many_info_results(client: TestClient, packages: list[Package]):
    # Make many of these packages depend and rely on each other.
    # This way, we can test to see that the exceeded limit stays true
    # regardless of the number of related records.
    with db.begin():
        for i in range(len(packages) - 1):
            db.create(
                PackageDependency,
                DepTypeID=DEPENDS_ID,
                Package=packages[i],
                DepName=packages[i + 1].Name,
            )
            db.create(
                PackageRelation,
                RelTypeID=PROVIDES_ID,
                Package=packages[i],
                RelName=packages[i + 1].Name,
            )

    config_getint = config.getint

    def mock_config(section: str, key: str):
        if key == "max_rpc_results":
            return 1
        return config_getint(section, key)

    params = {"v": 5, "type": "info", "arg[]": [p.Name for p in packages]}
    with mock.patch("aurweb.config.getint", side_effect=mock_config):
        with client as request:
            resp = request.get("/rpc", params=params)
    assert resp.json().get("error") == "Too many package results."


def test_rpc_openapi_info(client: TestClient, packages: list[Package]):
    pkgname = packages[0].Name

    with client as request:
        endp = f"/rpc/v5/info/{pkgname}"
        resp = request.get(endp)
    assert resp.status_code == HTTPStatus.OK

    data = resp.json()
    assert data.get("resultcount") == 1


def test_rpc_openapi_multiinfo(client: TestClient, packages: list[Package]):
    pkgname = packages[0].Name

    with client as request:
        endp = "/rpc/v5/info"
        resp = request.get(endp, params={"arg[]": [pkgname]})
    assert resp.status_code == HTTPStatus.OK

    data = resp.json()
    assert data.get("resultcount") == 1


def test_rpc_openapi_multiinfo_post(client: TestClient, packages: list[Package]):
    pkgname = packages[0].Name

    with client as request:
        endp = "/rpc/v5/info"
        resp = request.post(endp, json={"arg": [pkgname]})
    assert resp.status_code == HTTPStatus.OK

    data = resp.json()
    assert data.get("resultcount") == 1


def test_rpc_openapi_multiinfo_post_bad_request(
    client: TestClient, packages: list[Package]
):
    pkgname = packages[0].Name

    with client as request:
        endp = "/rpc/v5/info"
        resp = request.post(endp, json={"arg": pkgname})
    assert resp.status_code == HTTPStatus.BAD_REQUEST

    data = resp.json()
    expected = "the 'arg' parameter must be of array type"
    assert data.get("error") == expected


def test_rpc_openapi_search_arg(client: TestClient, packages: list[Package]):
    pkgname = packages[0].Name

    with client as request:
        endp = f"/rpc/v5/search/{pkgname}"
        resp = request.get(endp)
    assert resp.status_code == HTTPStatus.OK

    data = resp.json()
    assert data.get("resultcount") == 1


def test_rpc_openapi_search(client: TestClient, packages: list[Package]):
    pkgname = packages[0].Name

    with client as request:
        endp = "/rpc/v5/search"
        resp = request.get(endp, params={"arg": pkgname})
    assert resp.status_code == HTTPStatus.OK

    data = resp.json()
    assert data.get("resultcount") == 1


def test_rpc_openapi_search_post(client: TestClient, packages: list[Package]):
    pkgname = packages[0].Name

    with client as request:
        endp = "/rpc/v5/search"
        resp = request.post(endp, json={"arg": pkgname})
    assert resp.status_code == HTTPStatus.OK

    data = resp.json()
    assert data.get("resultcount") == 1


def test_rpc_openapi_search_post_bad_request(client: TestClient):
    # Test by parameter
    with client as request:
        endp = "/rpc/v5/search"
        resp = request.post(endp, json={"by": 1})
    assert resp.status_code == HTTPStatus.BAD_REQUEST
    data = resp.json()
    expected = "the 'by' parameter must be of string type"
    assert data.get("error") == expected

    # Test arg parameter
    with client as request:
        endp = "/rpc/v5/search"
        resp = request.post(endp, json={"arg": ["a", "list"]})
    assert resp.status_code == HTTPStatus.BAD_REQUEST
    data = resp.json()
    expected = "the 'arg' parameter must be of string type"
    assert data.get("error") == expected


def test_rpc_openapi_suggest(client: TestClient, packages: list[Package]):
    suggestions = {
        "big": ["big-chungus"],
        "chungy": ["chungy-chungus"],
    }

    for term, expected in suggestions.items():
        with client as request:
            endp = f"/rpc/v5/suggest/{term}"
            resp = request.get(endp)
        assert resp.status_code == HTTPStatus.OK

        data = resp.json()
        assert data == expected
