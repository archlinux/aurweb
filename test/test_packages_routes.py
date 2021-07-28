from datetime import datetime
from http import HTTPStatus

import pytest

from fastapi.testclient import TestClient

from aurweb import asgi, db
from aurweb.models.account_type import USER_ID, AccountType
from aurweb.models.dependency_type import DependencyType
from aurweb.models.official_provider import OfficialProvider
from aurweb.models.package import Package
from aurweb.models.package_base import PackageBase
from aurweb.models.package_comment import PackageComment
from aurweb.models.package_dependency import PackageDependency
from aurweb.models.package_keyword import PackageKeyword
from aurweb.models.package_relation import PackageRelation
from aurweb.models.relation_type import PROVIDES_ID, RelationType
from aurweb.models.user import User
from aurweb.testing import setup_test_db
from aurweb.testing.html import parse_root
from aurweb.testing.requests import Request


def package_endpoint(package: Package) -> str:
    return f"/packages/{package.Name}"


def create_package(pkgname: str, maintainer: User,
                   autocommit: bool = True) -> Package:
    pkgbase = db.create(PackageBase,
                        Name=pkgname,
                        Maintainer=maintainer,
                        autocommit=False)
    return db.create(Package, Name=pkgbase.Name, PackageBase=pkgbase,
                     autocommit=autocommit)


def create_package_dep(package: Package, depname: str,
                       dep_type_name: str = "depends",
                       autocommit: bool = True) -> PackageDependency:
    dep_type = db.query(DependencyType,
                        DependencyType.Name == dep_type_name).first()
    return db.create(PackageDependency,
                     DependencyType=dep_type,
                     Package=package,
                     DepName=depname,
                     autocommit=autocommit)


def create_package_rel(package: Package,
                       relname: str,
                       autocommit: bool = True) -> PackageRelation:
    rel_type = db.query(RelationType,
                        RelationType.ID == PROVIDES_ID).first()
    return db.create(PackageRelation,
                     RelationType=rel_type,
                     Package=package,
                     RelName=relname)


@pytest.fixture(autouse=True)
def setup():
    setup_test_db(
        User.__tablename__,
        Package.__tablename__,
        PackageBase.__tablename__,
        PackageDependency.__tablename__,
        PackageRelation.__tablename__,
        PackageKeyword.__tablename__,
        OfficialProvider.__tablename__
    )


@pytest.fixture
def client() -> TestClient:
    """ Yield a FastAPI TestClient. """
    yield TestClient(app=asgi.app)


@pytest.fixture
def user() -> User:
    """ Yield a user. """
    account_type = db.query(AccountType, AccountType.ID == USER_ID).first()
    yield db.create(User, Username="test",
                    Email="test@example.org",
                    Passwd="testPassword",
                    AccountType=account_type)


@pytest.fixture
def maintainer() -> User:
    """ Yield a specific User used to maintain packages. """
    account_type = db.query(AccountType, AccountType.ID == USER_ID).first()
    yield db.create(User, Username="test_maintainer",
                    Email="test_maintainer@example.org",
                    Passwd="testPassword",
                    AccountType=account_type)


@pytest.fixture
def package(maintainer: User) -> Package:
    """ Yield a Package created by user. """
    pkgbase = db.create(PackageBase,
                        Name="test-package",
                        Maintainer=maintainer)
    yield db.create(Package,
                    PackageBase=pkgbase,
                    Name=pkgbase.Name)


def test_package_not_found(client: TestClient):
    with client as request:
        resp = request.get("/packages/not_found")
    assert resp.status_code == int(HTTPStatus.NOT_FOUND)


def test_package_official_not_found(client: TestClient, package: Package):
    """ When a Package has a matching OfficialProvider record, it is not
    hosted on AUR, but in the official repositories. Getting a package
    with this kind of record should return a status code 404. """
    db.create(OfficialProvider,
              Name=package.Name,
              Repo="core",
              Provides=package.Name)

    with client as request:
        resp = request.get(package_endpoint(package))
    assert resp.status_code == int(HTTPStatus.NOT_FOUND)


def test_package(client: TestClient, package: Package):
    """ Test a single /packages/{name} route. """
    with client as request:

        resp = request.get(package_endpoint(package))
    assert resp.status_code == int(HTTPStatus.OK)

    root = parse_root(resp.text)
    h2 = root.find('.//div[@id="pkgdetails"]/h2')

    sections = h2.text.split(":")
    assert sections[0] == "Package Details"

    name, version = sections[1].lstrip().split(" ")
    assert name == package.Name
    version == package.Version

    rows = root.findall('.//table[@id="pkginfo"]//tr')
    row = rows[1]  # Second row is our target.

    pkgbase = row.find("./td/a")
    assert pkgbase.text.strip() == package.PackageBase.Name


def test_package_comments(client: TestClient, user: User, package: Package):
    now = (datetime.utcnow().timestamp())
    comment = db.create(PackageComment, PackageBase=package.PackageBase,
                        User=user, Comments="Test comment", CommentTS=now)

    cookies = {"AURSID": user.login(Request(), "testPassword")}
    with client as request:
        resp = request.get(package_endpoint(package), cookies=cookies)
    assert resp.status_code == int(HTTPStatus.OK)

    root = parse_root(resp.text)
    expected = [
        comment.Comments
    ]
    comments = root.xpath('.//div[contains(@class, "package-comments")]'
                          '/div[@class="article-content"]/div/text()')
    for i, row in enumerate(expected):
        assert comments[i].strip() == row


def test_package_authenticated(client: TestClient, user: User,
                               package: Package):
    """ We get the same here for either authenticated or not
    authenticated. Form inputs are presented to maintainers.
    This process also occurs when pkgbase.html is rendered. """
    cookies = {"AURSID": user.login(Request(), "testPassword")}
    with client as request:
        resp = request.get(package_endpoint(package), cookies=cookies)
    assert resp.status_code == int(HTTPStatus.OK)

    expected = [
        "View PKGBUILD",
        "View Changes",
        "Download snapshot",
        "Search wiki",
        "Flag package out-of-date",
        "Vote for this package",
        "Enable notifications",
        "Submit Request"
    ]
    for expected_text in expected:
        assert expected_text in resp.text


def test_package_authenticated_maintainer(client: TestClient,
                                          maintainer: User,
                                          package: Package):
    cookies = {"AURSID": maintainer.login(Request(), "testPassword")}
    with client as request:
        resp = request.get(package_endpoint(package), cookies=cookies)
    assert resp.status_code == int(HTTPStatus.OK)

    expected = [
        "View PKGBUILD",
        "View Changes",
        "Download snapshot",
        "Search wiki",
        "Flag package out-of-date",
        "Vote for this package",
        "Enable notifications",
        "Manage Co-Maintainers",
        "Submit Request",
        "Delete Package",
        "Merge Package",
        "Disown Package"
    ]
    for expected_text in expected:
        assert expected_text in resp.text


def test_package_dependencies(client: TestClient, maintainer: User,
                              package: Package):
    # Create a normal dependency of type depends.
    dep_pkg = create_package("test-dep-1", maintainer, autocommit=False)
    dep = create_package_dep(package, dep_pkg.Name, autocommit=False)

    # Also, create a makedepends.
    make_dep_pkg = create_package("test-dep-2", maintainer, autocommit=False)
    make_dep = create_package_dep(package, make_dep_pkg.Name,
                                  dep_type_name="makedepends",
                                  autocommit=False)

    # And... a checkdepends!
    check_dep_pkg = create_package("test-dep-3", maintainer, autocommit=False)
    check_dep = create_package_dep(package, check_dep_pkg.Name,
                                   dep_type_name="checkdepends",
                                   autocommit=False)

    # Geez. Just stop. This is optdepends.
    opt_dep_pkg = create_package("test-dep-4", maintainer, autocommit=False)
    opt_dep = create_package_dep(package, opt_dep_pkg.Name,
                                 dep_type_name="optdepends",
                                 autocommit=False)

    # Heh. Another optdepends to test one with a description.
    opt_desc_dep_pkg = create_package("test-dep-5", maintainer,
                                      autocommit=False)
    opt_desc_dep = create_package_dep(package, opt_desc_dep_pkg.Name,
                                      dep_type_name="optdepends",
                                      autocommit=False)
    opt_desc_dep.DepDesc = "Test description."

    broken_dep = create_package_dep(package, "test-dep-6",
                                    dep_type_name="depends",
                                    autocommit=False)

    # Create an official provider record.
    db.create(OfficialProvider, Name="test-dep-99",
              Repo="core", Provides="test-dep-99",
              autocommit=False)
    official_dep = create_package_dep(package, "test-dep-99",
                                      autocommit=False)

    # Also, create a provider who provides our test-dep-99.
    provider = create_package("test-provider", maintainer, autocommit=False)
    create_package_rel(provider, dep.DepName)

    with client as request:
        resp = request.get(package_endpoint(package))
    assert resp.status_code == int(HTTPStatus.OK)

    root = parse_root(resp.text)

    expected = [
        dep.DepName,
        make_dep.DepName,
        check_dep.DepName,
        opt_dep.DepName,
        opt_desc_dep.DepName,
        official_dep.DepName
    ]
    pkgdeps = root.findall('.//ul[@id="pkgdepslist"]/li/a')
    for i, expectation in enumerate(expected):
        assert pkgdeps[i].text.strip() == expectation

    broken_node = root.find('.//ul[@id="pkgdepslist"]/li/span')
    assert broken_node.text.strip() == broken_dep.DepName


def test_pkgbase_not_found(client: TestClient):
    with client as request:
        resp = request.get("/pkgbase/not_found")
    assert resp.status_code == int(HTTPStatus.NOT_FOUND)


def test_pkgbase_redirect(client: TestClient, package: Package):
    with client as request:
        resp = request.get(f"/pkgbase/{package.Name}",
                           allow_redirects=False)
    assert resp.status_code == int(HTTPStatus.SEE_OTHER)
    assert resp.headers.get("location") == f"/packages/{package.Name}"


def test_pkgbase(client: TestClient, package: Package):
    second = db.create(Package, Name="second-pkg",
                       PackageBase=package.PackageBase)

    expected = [package.Name, second.Name]
    with client as request:
        resp = request.get(f"/pkgbase/{package.Name}",
                           allow_redirects=False)
    assert resp.status_code == int(HTTPStatus.OK)

    root = parse_root(resp.text)

    # Check the details box title.
    title = root.find('.//div[@id="pkgdetails"]/h2')
    title, pkgname = title.text.split(": ")
    assert title == "Package Base Details"
    assert pkgname == package.Name

    pkgs = root.findall('.//div[@id="pkgs"]/ul/li/a')
    for i, name in enumerate(expected):
        assert pkgs[i].text.strip() == name
