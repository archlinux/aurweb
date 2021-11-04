import re

from http import HTTPStatus
from unittest import mock

import orjson
import pytest

from fastapi.testclient import TestClient
from redis.client import Pipeline

from aurweb import asgi, config, db, scripts
from aurweb.db import begin, create, query
from aurweb.models.account_type import AccountType
from aurweb.models.dependency_type import DependencyType
from aurweb.models.license import License
from aurweb.models.package import Package
from aurweb.models.package_base import PackageBase
from aurweb.models.package_dependency import PackageDependency
from aurweb.models.package_keyword import PackageKeyword
from aurweb.models.package_license import PackageLicense
from aurweb.models.package_relation import PackageRelation
from aurweb.models.package_vote import PackageVote
from aurweb.models.relation_type import RelationType
from aurweb.models.user import User
from aurweb.redis import redis_connection


@pytest.fixture
def client() -> TestClient:
    yield TestClient(app=asgi.app)


@pytest.fixture(autouse=True)
def setup(db_test):
    # TODO: Rework this into organized fixtures.

    # Create test package details.
    with begin():
        # Get ID types.
        account_type = query(AccountType, AccountType.AccountType == "User").first()

        dependency_depends = query(DependencyType, DependencyType.Name == "depends").first()
        dependency_optdepends = query(DependencyType, DependencyType.Name == "optdepends").first()
        dependency_makedepends = query(DependencyType, DependencyType.Name == "makedepends").first()
        dependency_checkdepends = query(DependencyType, DependencyType.Name == "checkdepends").first()

        relation_conflicts = query(RelationType, RelationType.Name == "conflicts").first()
        relation_provides = query(RelationType, RelationType.Name == "provides").first()
        relation_replaces = query(RelationType, RelationType.Name == "replaces").first()

        # Create database info.
        user1 = create(User,
                       Username="user1",
                       Email="user1@example.com",
                       RealName="Test User 1",
                       Passwd="testPassword",
                       AccountType=account_type)

        user2 = create(User,
                       Username="user2",
                       Email="user2@example.com",
                       RealName="Test User 2",
                       Passwd="testPassword",
                       AccountType=account_type)

        user3 = create(User,
                       Username="user3",
                       Email="user3@example.com",
                       RealName="Test User 3",
                       Passwd="testPassword",
                       AccountType=account_type)

        pkgbase1 = create(PackageBase, Name="big-chungus",
                          Maintainer=user1,
                          Packager=user1)

        pkgname1 = create(Package,
                          PackageBase=pkgbase1,
                          Name=pkgbase1.Name,
                          Description="Bunny bunny around bunny",
                          URL="https://example.com/")

        pkgbase2 = create(PackageBase, Name="chungy-chungus",
                          Maintainer=user1,
                          Packager=user1)

        pkgname2 = create(Package,
                          PackageBase=pkgbase2,
                          Name=pkgbase2.Name,
                          Description="Wubby wubby on wobba wuubu",
                          URL="https://example.com/")

        pkgbase3 = create(PackageBase, Name="gluggly-chungus",
                          Maintainer=user1,
                          Packager=user1)

        pkgbase4 = create(PackageBase, Name="fugly-chungus",
                          Maintainer=user1,
                          Packager=user1)

        desc = "A Package belonging to a PackageBase with another name."
        create(Package,
               PackageBase=pkgbase4,
               Name="other-pkg",
               Description=desc,
               URL="https://example.com")

        create(Package,
               PackageBase=pkgbase3,
               Name=pkgbase3.Name,
               Description="glurrba glurrba gur globba",
               URL="https://example.com/")

        pkgbase4 = create(PackageBase, Name="woogly-chungus")

        create(Package,
               PackageBase=pkgbase4,
               Name=pkgbase4.Name,
               Description="wuggla woblabeloop shemashmoop",
               URL="https://example.com/")

        # Dependencies.
        create(PackageDependency,
               Package=pkgname1,
               DependencyType=dependency_depends,
               DepName="chungus-depends")

        create(PackageDependency,
               Package=pkgname2,
               DependencyType=dependency_depends,
               DepName="chungy-depends")

        create(PackageDependency,
               Package=pkgname1,
               DependencyType=dependency_optdepends,
               DepName="chungus-optdepends",
               DepCondition="=50")

        create(PackageDependency,
               Package=pkgname1,
               DependencyType=dependency_makedepends,
               DepName="chungus-makedepends")

        create(PackageDependency,
               Package=pkgname1,
               DependencyType=dependency_checkdepends,
               DepName="chungus-checkdepends")

        # Relations.
        create(PackageRelation,
               Package=pkgname1,
               RelationType=relation_conflicts,
               RelName="chungus-conflicts")

        create(PackageRelation,
               Package=pkgname2,
               RelationType=relation_conflicts,
               RelName="chungy-conflicts")

        create(PackageRelation,
               Package=pkgname1,
               RelationType=relation_provides,
               RelName="chungus-provides",
               RelCondition="<=200")

        create(PackageRelation,
               Package=pkgname1,
               RelationType=relation_replaces,
               RelName="chungus-replaces",
               RelCondition="<=200")

        license = create(License, Name="GPL")

        create(PackageLicense,
               Package=pkgname1,
               License=license)

        for i in ["big-chungus", "smol-chungus", "sizeable-chungus"]:
            create(PackageKeyword,
                   PackageBase=pkgbase1,
                   Keyword=i)

        for i in [user1, user2, user3]:
            create(PackageVote,
                   User=i,
                   PackageBase=pkgbase1,
                   VoteTS=5000)

    conn = db.ConnectionExecutor(db.get_engine().raw_connection())
    scripts.popupdate.run_single(conn, pkgbase1)


@pytest.fixture
def pipeline():
    redis = redis_connection()
    pipeline = redis.pipeline()

    pipeline.delete("ratelimit-ws:testclient")
    pipeline.delete("ratelimit:testclient")
    one, two = pipeline.execute()

    yield pipeline


def test_rpc_singular_info(client: TestClient):
    # Define expected response.
    expected_data = {
        "version": 5,
        "results": [{
            "Name": "big-chungus",
            "Version": "",
            "Description": "Bunny bunny around bunny",
            "URL": "https://example.com/",
            "PackageBase": "big-chungus",
            "NumVotes": 3,
            "Popularity": 0.0,
            "OutOfDate": None,
            "Maintainer": "user1",
            "URLPath": "/cgit/aur.git/snapshot/big-chungus.tar.gz",
            "Depends": ["chungus-depends"],
            "OptDepends": ["chungus-optdepends=50"],
            "MakeDepends": ["chungus-makedepends"],
            "CheckDepends": ["chungus-checkdepends"],
            "Conflicts": ["chungus-conflicts"],
            "Provides": ["chungus-provides<=200"],
            "Replaces": ["chungus-replaces<=200"],
            "License": ["GPL"],
            "Keywords": [
                "big-chungus",
                "sizeable-chungus",
                "smol-chungus"
            ]
        }],
        "resultcount": 1,
        "type": "multiinfo"
    }

    # Make dummy request.
    with client as request:
        response_arg = request.get(
            "/rpc/?v=5&type=info&arg=chungy-chungus&arg=big-chungus")

    # Load  request response into Python dictionary.
    response_info_arg = orjson.loads(response_arg.content.decode())

    # Remove the FirstSubmitted LastModified, ID and PackageBaseID keys from
    # reponse, as the key's values aren't guaranteed to match between the two
    # (the keys are already removed from 'expected_data').
    for i in ["FirstSubmitted", "LastModified", "ID", "PackageBaseID"]:
        response_info_arg["results"][0].pop(i)

    # Validate that the new dictionaries are the same.
    assert response_info_arg == expected_data


def test_rpc_nonexistent_package(client: TestClient):
    # Make dummy request.
    with client as request:
        response = request.get("/rpc/?v=5&type=info&arg=nonexistent-package")

    # Load request response into Python dictionary.
    response_data = orjson.loads(response.content.decode())

    # Validate data.
    assert response_data["resultcount"] == 0


def test_rpc_multiinfo(client: TestClient):
    # Make dummy request.
    request_packages = ["big-chungus", "chungy-chungus"]
    with client as request:
        response = request.get(
            "/rpc/?v=5&type=info&arg[]=big-chungus&arg[]=chungy-chungus")

    # Load request response into Python dictionary.
    response_data = orjson.loads(response.content.decode())

    # Validate data.
    for i in response_data["results"]:
        request_packages.remove(i["Name"])

    assert request_packages == []


def test_rpc_mixedargs(client: TestClient):
    # Make dummy request.
    response1_packages = ["gluggly-chungus"]
    response2_packages = ["gluggly-chungus", "chungy-chungus"]

    with client as request:
        response1 = request.get(
            "/rpc?v=5&arg[]=big-chungus&arg=gluggly-chungus&type=info")
    assert response1.status_code == int(HTTPStatus.OK)

    with client as request:
        response2 = request.get(
            "/rpc?v=5&arg=big-chungus&arg[]=gluggly-chungus&type=info&arg[]=chungy-chungus")
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


def test_rpc_no_dependencies(client: TestClient):
    """This makes sure things like 'MakeDepends' get removed from JSON strings
    when they don't have set values."""

    expected_response = {
        'version': 5,
        'results': [{
            'Name': 'chungy-chungus',
            'Version': '',
            'Description': 'Wubby wubby on wobba wuubu',
            'URL': 'https://example.com/',
            'PackageBase': 'chungy-chungus',
            'NumVotes': 0,
            'Popularity': 0.0,
            'OutOfDate': None,
            'Maintainer': 'user1',
            'URLPath': '/cgit/aur.git/snapshot/chungy-chungus.tar.gz',
            'Depends': ['chungy-depends'],
            'Conflicts': ['chungy-conflicts'],
            'License': [],
            'Keywords': []
        }],
        'resultcount': 1,
        'type': 'multiinfo'
    }

    # Make dummy request.
    with client as request:
        response = request.get("/rpc/?v=5&type=info&arg=chungy-chungus")
    response_data = orjson.loads(response.content.decode())

    # Remove inconsistent keys.
    for i in ["ID", "PackageBaseID", "FirstSubmitted", "LastModified"]:
        response_data["results"][0].pop(i)

    assert response_data == expected_response


def test_rpc_bad_type(client: TestClient):
    # Define expected response.
    expected_data = {
        'version': 5,
        'results': [],
        'resultcount': 0,
        'type': 'error',
        'error': 'Incorrect request type specified.'
    }

    # Make dummy request.
    with client as request:
        response = request.get("/rpc/?v=5&type=invalid-type&arg=big-chungus")

    # Load  request response into Python dictionary.
    response_data = orjson.loads(response.content.decode())

    # Validate data.
    assert expected_data == response_data


def test_rpc_bad_version(client: TestClient):
    # Define expected response.
    expected_data = {
        'version': 0,
        'resultcount': 0,
        'results': [],
        'type': 'error',
        'error': 'Invalid version specified.'
    }

    # Make dummy request.
    with client as request:
        response = request.get("/rpc/?v=0&type=info&arg=big-chungus")

    # Load  request response into Python dictionary.
    response_data = orjson.loads(response.content.decode())

    # Validate data.
    assert expected_data == response_data


def test_rpc_no_version(client: TestClient):
    # Define expected response.
    expected_data = {
        'version': None,
        'resultcount': 0,
        'results': [],
        'type': 'error',
        'error': 'Please specify an API version.'
    }

    # Make dummy request.
    with client as request:
        response = request.get("/rpc/?type=info&arg=big-chungus")

    # Load  request response into Python dictionary.
    response_data = orjson.loads(response.content.decode())

    # Validate data.
    assert expected_data == response_data


def test_rpc_no_type(client: TestClient):
    # Define expected response.
    expected_data = {
        'version': 5,
        'results': [],
        'resultcount': 0,
        'type': 'error',
        'error': 'No request type/data specified.'
    }

    # Make dummy request.
    with client as request:
        response = request.get("/rpc/?v=5&arg=big-chungus")

    # Load  request response into Python dictionary.
    response_data = orjson.loads(response.content.decode())

    # Validate data.
    assert expected_data == response_data


def test_rpc_no_args(client: TestClient):
    # Define expected response.
    expected_data = {
        'version': 5,
        'results': [],
        'resultcount': 0,
        'type': 'error',
        'error': 'No request type/data specified.'
    }

    # Make dummy request.
    with client as request:
        response = request.get("/rpc/?v=5&type=info")

    # Load  request response into Python dictionary.
    response_data = orjson.loads(response.content.decode())

    # Validate data.
    assert expected_data == response_data


def test_rpc_no_maintainer(client: TestClient):
    # Make dummy request.
    with client as request:
        response = request.get("/rpc/?v=5&type=info&arg=woogly-chungus")

    # Load  request response into Python dictionary.
    response_data = orjson.loads(response.content.decode())

    # Validate data.
    assert response_data["results"][0]["Maintainer"] is None


def test_rpc_suggest_pkgbase(client: TestClient):
    with client as request:
        response = request.get("/rpc?v=5&type=suggest-pkgbase&arg=big")
    data = response.json()
    assert data == ["big-chungus"]

    with client as request:
        response = request.get("/rpc?v=5&type=suggest-pkgbase&arg=chungy")
    data = response.json()
    assert data == ["chungy-chungus"]

    # Test no arg supplied.
    with client as request:
        response = request.get("/rpc?v=5&type=suggest-pkgbase")
    data = response.json()
    assert data == []


def test_rpc_suggest(client: TestClient):
    with client as request:
        response = request.get("/rpc?v=5&type=suggest&arg=other")
    data = response.json()
    assert data == ["other-pkg"]

    # Test non-existent Package.
    with client as request:
        response = request.get("/rpc?v=5&type=suggest&arg=nonexistent")
    data = response.json()
    assert data == []

    # Test no arg supplied.
    with client as request:
        response = request.get("/rpc?v=5&type=suggest")
    data = response.json()
    assert data == []


def mock_config_getint(section: str, key: str):
    if key == "request_limit":
        return 4
    elif key == "window_length":
        return 100
    return config.getint(section, key)


@mock.patch("aurweb.config.getint", side_effect=mock_config_getint)
def test_rpc_ratelimit(getint: mock.MagicMock, client: TestClient,
                       pipeline: Pipeline):
    for i in range(4):
        # The first 4 requests should be good.
        with client as request:
            response = request.get("/rpc?v=5&type=suggest-pkgbase&arg=big")
        assert response.status_code == int(HTTPStatus.OK)

    # The fifth request should be banned.
    with client as request:
        response = request.get("/rpc?v=5&type=suggest-pkgbase&arg=big")
    assert response.status_code == int(HTTPStatus.TOO_MANY_REQUESTS)

    # Delete the cached records.
    pipeline.delete("ratelimit-ws:testclient")
    pipeline.delete("ratelimit:testclient")
    one, two = pipeline.execute()
    assert one and two

    # The new first request should be good.
    with client as request:
        response = request.get("/rpc?v=5&type=suggest-pkgbase&arg=big")
    assert response.status_code == int(HTTPStatus.OK)


def test_rpc_etag(client: TestClient):
    with client as request:
        response1 = request.get("/rpc?v=5&type=suggest-pkgbase&arg=big")

    with client as request:
        response2 = request.get("/rpc?v=5&type=suggest-pkgbase&arg=big")
    assert response1.headers.get("ETag") is not None
    assert response1.headers.get("ETag") != str()
    assert response1.headers.get("ETag") == response2.headers.get("ETag")


def test_rpc_search_arg_too_small(client: TestClient):
    with client as request:
        response = request.get("/rpc?v=5&type=search&arg=b")
    assert response.status_code == int(HTTPStatus.OK)
    assert response.json().get("error") == "Query arg too small."


def test_rpc_search(client: TestClient):
    with client as request:
        response = request.get("/rpc?v=5&type=search&arg=big")
    assert response.status_code == int(HTTPStatus.OK)

    data = response.json()
    assert data.get("resultcount") == 1

    result = data.get("results")[0]
    assert result.get("Name") == "big-chungus"

    # Test the If-None-Match headers.
    etag = response.headers.get("ETag").strip('"')
    headers = {"If-None-Match": etag}
    response = request.get("/rpc?v=5&type=search&arg=big", headers=headers)
    assert response.status_code == int(HTTPStatus.NOT_MODIFIED)
    assert response.content == b''

    # No args on non-m by types return an error.
    response = request.get("/rpc?v=5&type=search")
    assert response.json().get("error") == "No request type/data specified."


def test_rpc_msearch(client: TestClient):
    with client as request:
        response = request.get("/rpc?v=5&type=msearch&arg=user1")
    data = response.json()

    # user1 maintains 4 packages; assert that we got them all.
    assert data.get("resultcount") == 4
    names = list(sorted(r.get("Name") for r in data.get("results")))
    expected_results = list(sorted([
        "big-chungus",
        "chungy-chungus",
        "gluggly-chungus",
        "other-pkg"
    ]))
    assert names == expected_results

    # Search for a non-existent maintainer, giving us zero packages.
    response = request.get("/rpc?v=5&type=msearch&arg=blah-blah")
    data = response.json()
    assert data.get("resultcount") == 0

    # A missing arg still succeeds, but it returns all orphans.
    # Just verify that we receive no error and the orphaned result.
    response = request.get("/rpc?v=5&type=msearch")
    data = response.json()
    assert data.get("resultcount") == 1
    result = data.get("results")[0]
    assert result.get("Name") == "woogly-chungus"


def test_rpc_search_depends(client: TestClient):
    with client as request:
        response = request.get(
            "/rpc?v=5&type=search&by=depends&arg=chungus-depends")
    data = response.json()
    assert data.get("resultcount") == 1
    result = data.get("results")[0]
    assert result.get("Name") == "big-chungus"


def test_rpc_search_makedepends(client: TestClient):
    with client as request:
        response = request.get(
            "/rpc?v=5&type=search&by=makedepends&arg=chungus-makedepends")
    data = response.json()
    assert data.get("resultcount") == 1
    result = data.get("results")[0]
    assert result.get("Name") == "big-chungus"


def test_rpc_search_optdepends(client: TestClient):
    with client as request:
        response = request.get(
            "/rpc?v=5&type=search&by=optdepends&arg=chungus-optdepends")
    data = response.json()
    assert data.get("resultcount") == 1
    result = data.get("results")[0]
    assert result.get("Name") == "big-chungus"


def test_rpc_search_checkdepends(client: TestClient):
    with client as request:
        response = request.get(
            "/rpc?v=5&type=search&by=checkdepends&arg=chungus-checkdepends")
    data = response.json()
    assert data.get("resultcount") == 1
    result = data.get("results")[0]
    assert result.get("Name") == "big-chungus"


def test_rpc_incorrect_by(client: TestClient):
    with client as request:
        response = request.get("/rpc?v=5&type=search&by=fake&arg=big")
    assert response.json().get("error") == "Incorrect by field specified."


def test_rpc_jsonp_callback(client: TestClient):
    """ Test the callback parameter.

    For end-to-end verification, the `examples/jsonp.html` file can be
    used to submit jsonp callback requests to the RPC.
    """
    with client as request:
        response = request.get(
            "/rpc?v=5&type=search&arg=big&callback=jsonCallback")
    assert response.headers.get("content-type") == "text/javascript"
    assert re.search(r'^/\*\*/jsonCallback\(.*\)$', response.text) is not None

    # Test an invalid callback name; we get an application/json error.
    with client as request:
        response = request.get(
            "/rpc?v=5&type=search&arg=big&callback=jsonCallback!")
    assert response.headers.get("content-type") == "application/json"
    assert response.json().get("error") == "Invalid callback name."
