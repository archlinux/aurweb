import orjson
import pytest

from fastapi.testclient import TestClient

from aurweb.asgi import app
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
from aurweb.testing import setup_test_db


def make_request(path):
    with TestClient(app) as request:
        return request.get(path)


@pytest.fixture(autouse=True)
def setup():
    # Set up tables.
    setup_test_db("Users", "PackageBases", "Packages", "Licenses",
                  "PackageDepends", "PackageRelations", "PackageLicenses",
                  "PackageKeywords", "PackageVotes")

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


def test_rpc_singular_info():
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
    response_arg = make_request("/rpc/?v=5&type=info&arg=chungy-chungus&arg=big-chungus")

    # Load  request response into Python dictionary.
    response_info_arg = orjson.loads(response_arg.content.decode())

    # Remove the FirstSubmitted LastModified, ID and PackageBaseID keys from
    # reponse, as the key's values aren't guaranteed to match between the two
    # (the keys are already removed from 'expected_data').
    for i in ["FirstSubmitted", "LastModified", "ID", "PackageBaseID"]:
        response_info_arg["results"][0].pop(i)

    # Validate that the new dictionaries are the same.
    assert response_info_arg == expected_data


def test_rpc_nonexistent_package():
    # Make dummy request.
    response = make_request("/rpc/?v=5&type=info&arg=nonexistent-package")

    # Load request response into Python dictionary.
    response_data = orjson.loads(response.content.decode())

    # Validate data.
    assert response_data["resultcount"] == 0


def test_rpc_multiinfo():
    # Make dummy request.
    request_packages = ["big-chungus", "chungy-chungus"]
    response = make_request("/rpc/?v=5&type=info&arg[]=big-chungus&arg[]=chungy-chungus")

    # Load request response into Python dictionary.
    response_data = orjson.loads(response.content.decode())

    # Validate data.
    for i in response_data["results"]:
        request_packages.remove(i["Name"])

    assert request_packages == []


def test_rpc_mixedargs():
    # Make dummy request.
    response1_packages = ["gluggly-chungus"]
    response2_packages = ["gluggly-chungus", "chungy-chungus"]

    response1 = make_request("/rpc/?v=5&arg[]=big-chungus&arg=gluggly-chungus&type=info")
    response2 = make_request("/rpc/?v=5&arg=big-chungus&arg[]=gluggly-chungus&type=info&arg[]=chungy-chungus")

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


def test_rpc_no_dependencies():
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
            'NumVotes': 3,
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
    response = make_request("/rpc/?v=5&type=info&arg=chungy-chungus")
    response_data = orjson.loads(response.content.decode())

    # Remove inconsistent keys.
    for i in ["ID", "PackageBaseID", "FirstSubmitted", "LastModified"]:
        response_data["results"][0].pop(i)

    assert response_data == expected_response


def test_rpc_bad_type():
    # Define expected response.
    expected_data = {
        'version': 5,
        'results': [],
        'resultcount': 0,
        'type': 'error',
        'error': 'Incorrect request type specified.'
    }

    # Make dummy request.
    response = make_request("/rpc/?v=5&type=invalid-type&arg=big-chungus")

    # Load  request response into Python dictionary.
    response_data = orjson.loads(response.content.decode())

    # Validate data.
    assert expected_data == response_data


def test_rpc_bad_version():
    # Define expected response.
    expected_data = {
        'version': 0,
        'resultcount': 0,
        'results': [],
        'type': 'error',
        'error': 'Invalid version specified.'
    }

    # Make dummy request.
    response = make_request("/rpc/?v=0&type=info&arg=big-chungus")

    # Load  request response into Python dictionary.
    response_data = orjson.loads(response.content.decode())

    # Validate data.
    assert expected_data == response_data


def test_rpc_no_version():
    # Define expected response.
    expected_data = {
        'version': None,
        'resultcount': 0,
        'results': [],
        'type': 'error',
        'error': 'Please specify an API version.'
    }

    # Make dummy request.
    response = make_request("/rpc/?type=info&arg=big-chungus")

    # Load  request response into Python dictionary.
    response_data = orjson.loads(response.content.decode())

    # Validate data.
    assert expected_data == response_data


def test_rpc_no_type():
    # Define expected response.
    expected_data = {
        'version': 5,
        'results': [],
        'resultcount': 0,
        'type': 'error',
        'error': 'No request type/data specified.'
    }

    # Make dummy request.
    response = make_request("/rpc/?v=5&arg=big-chungus")

    # Load  request response into Python dictionary.
    response_data = orjson.loads(response.content.decode())

    # Validate data.
    assert expected_data == response_data


def test_rpc_no_args():
    # Define expected response.
    expected_data = {
        'version': 5,
        'results': [],
        'resultcount': 0,
        'type': 'error',
        'error': 'No request type/data specified.'
    }

    # Make dummy request.
    response = make_request("/rpc/?v=5&type=info")

    # Load  request response into Python dictionary.
    response_data = orjson.loads(response.content.decode())

    # Validate data.
    assert expected_data == response_data


def test_rpc_no_maintainer():
    # Make dummy request.
    response = make_request("/rpc/?v=5&type=info&arg=woogly-chungus")

    # Load  request response into Python dictionary.
    response_data = orjson.loads(response.content.decode())

    # Validate data.
    assert response_data["results"][0]["Maintainer"] is None


def test_rpc_suggest_pkgbase():
    response = make_request("/rpc?v=5&type=suggest-pkgbase&arg=big")
    data = response.json()
    assert data == ["big-chungus"]

    response = make_request("/rpc?v=5&type=suggest-pkgbase&arg=chungy")
    data = response.json()
    assert data == ["chungy-chungus"]
