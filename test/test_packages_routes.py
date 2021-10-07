import re

from datetime import datetime
from http import HTTPStatus
from typing import List

import pytest

from fastapi.testclient import TestClient

from aurweb import asgi, db, defaults
from aurweb.models.account_type import USER_ID, AccountType
from aurweb.models.dependency_type import DependencyType
from aurweb.models.official_provider import OfficialProvider
from aurweb.models.package import Package
from aurweb.models.package_base import PackageBase
from aurweb.models.package_comaintainer import PackageComaintainer
from aurweb.models.package_comment import PackageComment
from aurweb.models.package_dependency import PackageDependency
from aurweb.models.package_keyword import PackageKeyword
from aurweb.models.package_notification import PackageNotification
from aurweb.models.package_relation import PackageRelation
from aurweb.models.package_request import ACCEPTED_ID, REJECTED_ID, PackageRequest
from aurweb.models.package_vote import PackageVote
from aurweb.models.relation_type import PROVIDES_ID, RelationType
from aurweb.models.request_type import DELETION_ID, RequestType
from aurweb.models.user import User
from aurweb.testing import setup_test_db
from aurweb.testing.html import parse_root
from aurweb.testing.requests import Request


def package_endpoint(package: Package) -> str:
    return f"/packages/{package.Name}"


def create_package(pkgname: str, maintainer: User) -> Package:
    pkgbase = db.create(PackageBase,
                        Name=pkgname,
                        Maintainer=maintainer)
    return db.create(Package, Name=pkgbase.Name, PackageBase=pkgbase)


def create_package_dep(package: Package, depname: str,
                       dep_type_name: str = "depends") -> PackageDependency:
    dep_type = db.query(DependencyType,
                        DependencyType.Name == dep_type_name).first()
    return db.create(PackageDependency,
                     DependencyType=dep_type,
                     Package=package,
                     DepName=depname)


def create_package_rel(package: Package,
                       relname: str) -> PackageRelation:
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
        PackageVote.__tablename__,
        PackageNotification.__tablename__,
        PackageComaintainer.__tablename__,
        PackageComment.__tablename__,
        PackageRequest.__tablename__,
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
    with db.begin():
        user = db.create(User, Username="test",
                         Email="test@example.org",
                         Passwd="testPassword",
                         AccountType=account_type)
    yield user


@pytest.fixture
def maintainer() -> User:
    """ Yield a specific User used to maintain packages. """
    account_type = db.query(AccountType, AccountType.ID == USER_ID).first()
    with db.begin():
        maintainer = db.create(User, Username="test_maintainer",
                               Email="test_maintainer@example.org",
                               Passwd="testPassword",
                               AccountType=account_type)
    yield maintainer


@pytest.fixture
def tu_user():
    tu_type = db.query(AccountType,
                       AccountType.AccountType == "Trusted User").first()
    with db.begin():
        tu_user = db.create(User, Username="test_tu",
                            Email="test_tu@example.org",
                            RealName="Test TU", Passwd="testPassword",
                            AccountType=tu_type)
    yield tu_user


@pytest.fixture
def package(maintainer: User) -> Package:
    """ Yield a Package created by user. """
    now = int(datetime.utcnow().timestamp())
    with db.begin():
        pkgbase = db.create(PackageBase,
                            Name="test-package",
                            Maintainer=maintainer,
                            Packager=maintainer,
                            Submitter=maintainer,
                            ModifiedTS=now)
        package = db.create(Package,
                            PackageBase=pkgbase,
                            Name=pkgbase.Name)
    yield package


@pytest.fixture
def comment(user: User, package: Package) -> PackageComment:
    pkgbase = package.PackageBase
    now = int(datetime.utcnow().timestamp())
    with db.begin():
        comment = db.create(PackageComment,
                            User=user,
                            PackageBase=pkgbase,
                            Comments="Test comment.",
                            RenderedComment=str(),
                            CommentTS=now)
    yield comment


@pytest.fixture
def packages(maintainer: User) -> List[Package]:
    """ Yield 55 packages named pkg_0 .. pkg_54. """
    packages_ = []
    now = int(datetime.utcnow().timestamp())
    with db.begin():
        for i in range(55):
            pkgbase = db.create(PackageBase,
                                Name=f"pkg_{i}",
                                Maintainer=maintainer,
                                Packager=maintainer,
                                Submitter=maintainer,
                                ModifiedTS=now)
            package = db.create(Package,
                                PackageBase=pkgbase,
                                Name=f"pkg_{i}")
            packages_.append(package)

    yield packages_


@pytest.fixture
def requests(user: User, packages: List[Package]) -> List[PackageRequest]:
    pkgreqs = []
    deletion_type = db.query(RequestType).filter(
        RequestType.ID == DELETION_ID
    ).first()
    with db.begin():
        for i in range(55):
            pkgreq = db.create(PackageRequest,
                               RequestType=deletion_type,
                               User=user,
                               PackageBase=packages[i].PackageBase,
                               PackageBaseName=packages[i].Name,
                               Comments=f"Deletion request for pkg_{i}",
                               ClosureComment=str())
            pkgreqs.append(pkgreq)
    yield pkgreqs


def test_package_not_found(client: TestClient):
    with client as request:
        resp = request.get("/packages/not_found")
    assert resp.status_code == int(HTTPStatus.NOT_FOUND)


def test_package_official_not_found(client: TestClient, package: Package):
    """ When a Package has a matching OfficialProvider record, it is not
    hosted on AUR, but in the official repositories. Getting a package
    with this kind of record should return a status code 404. """
    with db.begin():
        db.create(OfficialProvider,
                  Name=package.Name,
                  Repo="core",
                  Provides=package.Name)

    with client as request:
        resp = request.get(package_endpoint(package))
    assert resp.status_code == int(HTTPStatus.NOT_FOUND)


def test_package(client: TestClient, package: Package):
    """ Test a single / packages / {name} route. """
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
    with db.begin():
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


def test_package_requests_display(client: TestClient, user: User,
                                  package: Package):
    type_ = db.query(RequestType, RequestType.ID == DELETION_ID).first()
    with db.begin():
        db.create(PackageRequest, PackageBase=package.PackageBase,
                  PackageBaseName=package.PackageBase.Name,
                  User=user, RequestType=type_,
                  Comments="Test comment.",
                  ClosureComment=str())

    # Test that a single request displays "1 pending request".
    with client as request:
        resp = request.get(package_endpoint(package))
    assert resp.status_code == int(HTTPStatus.OK)

    root = parse_root(resp.text)
    selector = '//div[@id="actionlist"]/ul/li/span[@class="flagged"]'
    target = root.xpath(selector)[0]
    assert target.text.strip() == "1 pending request"

    type_ = db.query(RequestType, RequestType.ID == DELETION_ID).first()
    with db.begin():
        db.create(PackageRequest, PackageBase=package.PackageBase,
                  PackageBaseName=package.PackageBase.Name,
                  User=user, RequestType=type_,
                  Comments="Test comment2.",
                  ClosureComment=str())

    # Test that a two requests display "2 pending requests".
    with client as request:
        resp = request.get(package_endpoint(package))
    assert resp.status_code == int(HTTPStatus.OK)

    root = parse_root(resp.text)
    selector = '//div[@id="actionlist"]/ul/li/span[@class="flagged"]'
    target = root.xpath(selector)[0]
    assert target.text.strip() == "2 pending requests"


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

    # When no requests are up, make sure we don't see the display for them.
    root = parse_root(resp.text)
    selector = '//div[@id="actionlist"]/ul/li/span[@class="flagged"]'
    target = root.xpath(selector)
    assert len(target) == 0


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
        "Disown Package"
    ]
    for expected_text in expected:
        assert expected_text in resp.text


def test_package_authenticated_tu(client: TestClient,
                                  tu_user: User,
                                  package: Package):
    cookies = {"AURSID": tu_user.login(Request(), "testPassword")}
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
    with db.begin():
        dep_pkg = create_package("test-dep-1", maintainer)
        dep = create_package_dep(package, dep_pkg.Name)
        dep.DepArch = "x86_64"

        # Also, create a makedepends.
        make_dep_pkg = create_package("test-dep-2", maintainer)
        make_dep = create_package_dep(package, make_dep_pkg.Name,
                                      dep_type_name="makedepends")

        # And... a checkdepends!
        check_dep_pkg = create_package("test-dep-3", maintainer)
        check_dep = create_package_dep(package, check_dep_pkg.Name,
                                       dep_type_name="checkdepends")

        # Geez. Just stop. This is optdepends.
        opt_dep_pkg = create_package("test-dep-4", maintainer)
        opt_dep = create_package_dep(package, opt_dep_pkg.Name,
                                     dep_type_name="optdepends")

        # Heh. Another optdepends to test one with a description.
        opt_desc_dep_pkg = create_package("test-dep-5", maintainer)
        opt_desc_dep = create_package_dep(package, opt_desc_dep_pkg.Name,
                                          dep_type_name="optdepends")
        opt_desc_dep.DepDesc = "Test description."

        broken_dep = create_package_dep(package, "test-dep-6",
                                        dep_type_name="depends")

        # Create an official provider record.
        db.create(OfficialProvider, Name="test-dep-99",
                  Repo="core", Provides="test-dep-99")
        official_dep = create_package_dep(package, "test-dep-99")

        # Also, create a provider who provides our test-dep-99.
        provider = create_package("test-provider", maintainer)
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

    # Let's make sure the DepArch was displayed for our first dep.
    arch = root.findall('.//ul[@id="pkgdepslist"]/li')[0]
    arch = arch.xpath('./em')[1]
    assert arch.text.strip() == "(x86_64)"

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
    with db.begin():
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


def test_packages(client: TestClient, packages: List[Package]):
    """ Test the / packages route with defaults.

    Defaults:
        50 results per page
        offset of 0
    """
    with client as request:
        response = request.get("/packages", params={
            "SeB": "X"  # "X" isn't valid, defaults to "nd"
        })
    assert response.status_code == int(HTTPStatus.OK)

    root = parse_root(response.text)
    stats = root.xpath('//div[@class="pkglist-stats"]/p')[0]
    pager_text = re.sub(r'\s+', " ", stats.text.replace("\n", "").strip())
    assert pager_text == "55 packages found. Page 1 of 2."

    rows = root.xpath('//table[@class="results"]/tbody/tr')
    assert len(rows) == 50  # Default per-page


def test_packages_search_by_name(client: TestClient, packages: List[Package]):
    with client as request:
        response = request.get("/packages", params={
            "SeB": "n",
            "K": "pkg_"
        })
    assert response.status_code == int(HTTPStatus.OK)

    root = parse_root(response.text)

    rows = root.xpath('//table[@class="results"]/tbody/tr')
    assert len(rows) == 50  # Default per-page


def test_packages_search_by_exact_name(client: TestClient,
                                       packages: List[Package]):
    with client as request:
        response = request.get("/packages", params={
            "SeB": "N",
            "K": "pkg_"
        })
    assert response.status_code == int(HTTPStatus.OK)

    root = parse_root(response.text)
    rows = root.xpath('//table[@class="results"]/tbody/tr')

    # There is no package named exactly 'pkg_', we get 0 results.
    assert len(rows) == 0

    with client as request:
        response = request.get("/packages", params={
            "SeB": "N",
            "K": "pkg_1"
        })
    assert response.status_code == int(HTTPStatus.OK)

    root = parse_root(response.text)
    rows = root.xpath('//table[@class="results"]/tbody/tr')

    # There's just one package named 'pkg_1', we get 1 result.
    assert len(rows) == 1


def test_packages_search_by_pkgbase(client: TestClient,
                                    packages: List[Package]):
    with client as request:
        response = request.get("/packages", params={
            "SeB": "b",
            "K": "pkg_"
        })
    assert response.status_code == int(HTTPStatus.OK)

    root = parse_root(response.text)

    rows = root.xpath('//table[@class="results"]/tbody/tr')
    assert len(rows) == 50


def test_packages_search_by_exact_pkgbase(client: TestClient,
                                          packages: List[Package]):
    with client as request:
        response = request.get("/packages", params={
            "SeB": "B",
            "K": "pkg_"
        })
    assert response.status_code == int(HTTPStatus.OK)

    root = parse_root(response.text)
    rows = root.xpath('//table[@class="results"]/tbody/tr')
    assert len(rows) == 0

    with client as request:
        response = request.get("/packages", params={
            "SeB": "B",
            "K": "pkg_1"
        })
    assert response.status_code == int(HTTPStatus.OK)

    root = parse_root(response.text)
    rows = root.xpath('//table[@class="results"]/tbody/tr')
    assert len(rows) == 1


def test_packages_search_by_keywords(client: TestClient,
                                     packages: List[Package]):
    # None of our packages have keywords, so this query should return nothing.
    with client as request:
        response = request.get("/packages", params={
            "SeB": "k",
            "K": "testKeyword"
        })
    assert response.status_code == int(HTTPStatus.OK)

    root = parse_root(response.text)
    rows = root.xpath('//table[@class="results"]/tbody/tr')
    assert len(rows) == 0

    # But now, let's create the keyword for the first package.
    package = packages[0]
    with db.begin():
        db.create(PackageKeyword,
                  PackageBase=package.PackageBase,
                  Keyword="testKeyword")

    # And request packages with that keyword, we should get 1 result.
    with client as request:
        response = request.get("/packages", params={
            "SeB": "k",
            "K": "testKeyword"
        })
    assert response.status_code == int(HTTPStatus.OK)

    root = parse_root(response.text)
    rows = root.xpath('//table[@class="results"]/tbody/tr')
    assert len(rows) == 1


def test_packages_search_by_maintainer(client: TestClient,
                                       maintainer: User,
                                       package: Package):
    with client as request:
        response = request.get("/packages", params={
            "SeB": "m",
            "K": maintainer.Username
        })
    assert response.status_code == int(HTTPStatus.OK)

    root = parse_root(response.text)
    rows = root.xpath('//table[@class="results"]/tbody/tr')
    assert len(rows) == 1


def test_packages_search_by_comaintainer(client: TestClient,
                                         maintainer: User,
                                         package: Package):
    # Nobody's a comaintainer yet.
    with client as request:
        response = request.get("/packages", params={
            "SeB": "c",
            "K": maintainer.Username
        })
    assert response.status_code == int(HTTPStatus.OK)

    root = parse_root(response.text)
    rows = root.xpath('//table[@class="results"]/tbody/tr')
    assert len(rows) == 0

    # Now, we create a comaintainer.
    with db.begin():
        db.create(PackageComaintainer,
                  PackageBase=package.PackageBase,
                  User=maintainer,
                  Priority=1)

    # Then test that it's returned by our search.
    with client as request:
        response = request.get("/packages", params={
            "SeB": "c",
            "K": maintainer.Username
        })
    assert response.status_code == int(HTTPStatus.OK)

    root = parse_root(response.text)
    rows = root.xpath('//table[@class="results"]/tbody/tr')
    assert len(rows) == 1


def test_packages_search_by_co_or_maintainer(client: TestClient,
                                             maintainer: User,
                                             package: Package):
    with client as request:
        response = request.get("/packages", params={
            "SeB": "M",
            "SB": "BLAH",  # Invalid SB; gets reset to default "n".
            "K": maintainer.Username
        })
    assert response.status_code == int(HTTPStatus.OK)

    root = parse_root(response.text)
    rows = root.xpath('//table[@class="results"]/tbody/tr')
    assert len(rows) == 1

    with db.begin():
        user = db.create(User, Username="comaintainer",
                         Email="comaintainer@example.org",
                         Passwd="testPassword")
        db.create(PackageComaintainer,
                  PackageBase=package.PackageBase,
                  User=user,
                  Priority=1)

    with client as request:
        response = request.get("/packages", params={
            "SeB": "M",
            "K": user.Username
        })
    assert response.status_code == int(HTTPStatus.OK)

    root = parse_root(response.text)
    rows = root.xpath('//table[@class="results"]/tbody/tr')
    assert len(rows) == 1


def test_packages_search_by_submitter(client: TestClient,
                                      maintainer: User,
                                      package: Package):
    with client as request:
        response = request.get("/packages", params={
            "SeB": "s",
            "K": maintainer.Username
        })
    assert response.status_code == int(HTTPStatus.OK)

    root = parse_root(response.text)
    rows = root.xpath('//table[@class="results"]/tbody/tr')
    assert len(rows) == 1


def test_packages_sort_by_votes(client: TestClient,
                                maintainer: User,
                                packages: List[Package]):
    # Set the first package's NumVotes to 1.
    with db.begin():
        packages[0].PackageBase.NumVotes = 1

    # Test that, by default, the first result is what we just set above.
    with client as request:
        response = request.get("/packages", params={
            "SB": "v"  # Votes.
        })
    assert response.status_code == int(HTTPStatus.OK)

    root = parse_root(response.text)
    rows = root.xpath('//table[@class="results"]/tbody/tr')
    votes = rows[0].xpath('./td')[2]  # The third column of the first row.
    assert votes.text.strip() == "1"

    # Now, test that with an ascending order, the last result is
    # the one we set, since the default (above) is descending.
    with client as request:
        response = request.get("/packages", params={
            "SB": "v",  # Votes.
            "SO": "a",  # Ascending.
            "O": "50"  # Second page.
        })
    assert response.status_code == int(HTTPStatus.OK)

    root = parse_root(response.text)
    rows = root.xpath('//table[@class="results"]/tbody/tr')
    votes = rows[-1].xpath('./td')[2]  # The third column of the last row.
    assert votes.text.strip() == "1"


def test_packages_sort_by_popularity(client: TestClient,
                                     maintainer: User,
                                     packages: List[Package]):
    # Set the first package's Popularity to 0.50.
    with db.begin():
        packages[0].PackageBase.Popularity = "0.50"

    # Test that, by default, the first result is what we just set above.
    with client as request:
        response = request.get("/packages", params={
            "SB": "p"  # Popularity
        })
    assert response.status_code == int(HTTPStatus.OK)

    root = parse_root(response.text)
    rows = root.xpath('//table[@class="results"]/tbody/tr')
    pop = rows[0].xpath('./td')[3]  # The fourth column of the first row.
    assert pop.text.strip() == "0.50"


def test_packages_sort_by_voted(client: TestClient,
                                maintainer: User,
                                packages: List[Package]):
    now = int(datetime.utcnow().timestamp())
    with db.begin():
        db.create(PackageVote, PackageBase=packages[0].PackageBase,
                  User=maintainer, VoteTS=now)

    # Test that, by default, the first result is what we just set above.
    cookies = {"AURSID": maintainer.login(Request(), "testPassword")}
    with client as request:
        response = request.get("/packages", params={
            "SB": "w",  # Voted
            "SO": "d"  # Descending, Voted first.
        }, cookies=cookies)
    assert response.status_code == int(HTTPStatus.OK)

    root = parse_root(response.text)
    rows = root.xpath('//table[@class="results"]/tbody/tr')
    voted = rows[0].xpath('./td')[5]  # The sixth column of the first row.
    assert voted.text.strip() == "Yes"

    # Conversely, everything else was not voted on.
    voted = rows[1].xpath('./td')[5]  # The sixth column of the second row.
    assert voted.text.strip() == str()  # Empty.


def test_packages_sort_by_notify(client: TestClient,
                                 maintainer: User,
                                 packages: List[Package]):
    db.create(PackageNotification,
              PackageBase=packages[0].PackageBase,
              User=maintainer)

    # Test that, by default, the first result is what we just set above.
    cookies = {"AURSID": maintainer.login(Request(), "testPassword")}
    with client as request:
        response = request.get("/packages", params={
            "SB": "o",  # Voted
            "SO": "d"  # Descending, Voted first.
        }, cookies=cookies)
    assert response.status_code == int(HTTPStatus.OK)

    root = parse_root(response.text)
    rows = root.xpath('//table[@class="results"]/tbody/tr')
    notify = rows[0].xpath('./td')[6]  # The sixth column of the first row.
    assert notify.text.strip() == "Yes"

    # Conversely, everything else was not voted on.
    notify = rows[1].xpath('./td')[6]  # The sixth column of the second row.
    assert notify.text.strip() == str()  # Empty.


def test_packages_sort_by_maintainer(client: TestClient,
                                     maintainer: User,
                                     package: Package):
    """ Sort a package search by the maintainer column. """

    # Create a second package, so the two can be ordered and checked.
    with db.begin():
        maintainer2 = db.create(User, Username="maintainer2",
                                Email="maintainer2@example.org",
                                Passwd="testPassword")
        base2 = db.create(PackageBase, Name="pkg_2", Maintainer=maintainer2,
                          Submitter=maintainer2, Packager=maintainer2)
        db.create(Package, Name="pkg_2", PackageBase=base2)

    # Check the descending order route.
    with client as request:
        response = request.get("/packages", params={
            "SB": "m",
            "SO": "d"
        })
    assert response.status_code == int(HTTPStatus.OK)

    root = parse_root(response.text)
    rows = root.xpath('//table[@class="results"]/tbody/tr')
    col = rows[0].xpath('./td')[5].xpath('./a')[0]  # Last column.

    assert col.text.strip() == maintainer.Username

    # On the other hand, with ascending, we should get reverse ordering.
    with client as request:
        response = request.get("/packages", params={
            "SB": "m",
            "SO": "a"
        })
    assert response.status_code == int(HTTPStatus.OK)

    root = parse_root(response.text)
    rows = root.xpath('//table[@class="results"]/tbody/tr')
    col = rows[0].xpath('./td')[5].xpath('./a')[0]  # Last column.

    assert col.text.strip() == maintainer2.Username


def test_packages_sort_by_last_modified(client: TestClient,
                                        packages: List[Package]):
    now = int(datetime.utcnow().timestamp())
    # Set the first package's ModifiedTS to be 1000 seconds before now.
    package = packages[0]
    with db.begin():
        package.PackageBase.ModifiedTS = now - 1000

    with client as request:
        response = request.get("/packages", params={
            "SB": "l",
            "SO": "a"  # Ascending; oldest modification first.
        })
    assert response.status_code == int(HTTPStatus.OK)

    # We should have 50 (default per page) results.
    root = parse_root(response.text)
    rows = root.xpath('//table[@class="results"]/tbody/tr')
    assert len(rows) == 50

    # Let's assert that the first item returned was the one we modified above.
    row = rows[0]
    col = row.xpath('./td')[0].xpath('./a')[0]
    assert col.text.strip() == package.Name


def test_packages_flagged(client: TestClient, maintainer: User,
                          packages: List[Package]):
    package = packages[0]

    now = int(datetime.utcnow().timestamp())

    with db.begin():
        package.PackageBase.OutOfDateTS = now
        package.PackageBase.Flagger = maintainer

    with client as request:
        response = request.get("/packages", params={
            "outdated": "on"
        })
    assert response.status_code == int(HTTPStatus.OK)

    # We should only get one result from this query; the package we flagged.
    root = parse_root(response.text)
    rows = root.xpath('//table[@class="results"]/tbody/tr')
    assert len(rows) == 1

    with client as request:
        response = request.get("/packages", params={
            "outdated": "off"
        })
    assert response.status_code == int(HTTPStatus.OK)

    # In this case, we should get 54 results, which means that the first
    # page will have 50 results (55 packages - 1 outdated = 54 not outdated).
    root = parse_root(response.text)
    rows = root.xpath('//table[@class="results"]/tbody/tr')
    assert len(rows) == 50


def test_packages_orphans(client: TestClient, packages: List[Package]):
    package = packages[0]
    with db.begin():
        package.PackageBase.Maintainer = None

    with client as request:
        response = request.get("/packages", params={"submit": "Orphans"})
    assert response.status_code == int(HTTPStatus.OK)

    # We only have one orphan. Let's make sure that's what is returned.
    root = parse_root(response.text)
    rows = root.xpath('//table[@class="results"]/tbody/tr')
    assert len(rows) == 1


def test_packages_per_page(client: TestClient, maintainer: User):
    """ Test the ability for /packages to deal with the PP query
    argument specifications (50, 100, 250; default: 50). """
    with db.begin():
        for i in range(255):
            base = db.create(PackageBase, Name=f"pkg_{i}",
                             Maintainer=maintainer,
                             Submitter=maintainer,
                             Packager=maintainer)
            db.create(Package, PackageBase=base, Name=base.Name)

    # Test default case, PP of 50.
    with client as request:
        response = request.get("/packages", params={"PP": 50})
    assert response.status_code == int(HTTPStatus.OK)
    root = parse_root(response.text)
    rows = root.xpath('//table[@class="results"]/tbody/tr')
    assert len(rows) == 50

    # Alright, test the next case, PP of 100.
    with client as request:
        response = request.get("/packages", params={"PP": 100})
    assert response.status_code == int(HTTPStatus.OK)
    root = parse_root(response.text)
    rows = root.xpath('//table[@class="results"]/tbody/tr')
    assert len(rows) == 100

    # And finally, the last case, a PP of 250.
    with client as request:
        response = request.get("/packages", params={"PP": 250})
    assert response.status_code == int(HTTPStatus.OK)
    root = parse_root(response.text)
    rows = root.xpath('//table[@class="results"]/tbody/tr')
    assert len(rows) == 250


def test_pkgbase_voters(client: TestClient, maintainer: User, package: Package):
    pkgbase = package.PackageBase
    endpoint = f"/pkgbase/{pkgbase.Name}/voters"

    now = int(datetime.utcnow().timestamp())
    with db.begin():
        db.create(PackageVote, User=maintainer, PackageBase=pkgbase,
                  VoteTS=now)

    with client as request:
        resp = request.get(endpoint)
    assert resp.status_code == int(HTTPStatus.OK)

    root = parse_root(resp.text)
    rows = root.xpath('//div[@class="box"]//ul/li')
    assert len(rows) == 1


def test_pkgbase_comment_not_found(client: TestClient, maintainer: User,
                                   package: Package):
    cookies = {"AURSID": maintainer.login(Request(), "testPassword")}
    comment_id = 12345  # A non-existing comment.
    endpoint = f"/pkgbase/{package.PackageBase.Name}/comments/{comment_id}"
    with client as request:
        resp = request.post(endpoint, data={
            "comment": "Failure"
        }, cookies=cookies)
    assert resp.status_code == int(HTTPStatus.NOT_FOUND)


def test_pkgbase_comment_form_unauthorized(client: TestClient, user: User,
                                           maintainer: User, package: Package):
    now = int(datetime.utcnow().timestamp())
    with db.begin():
        comment = db.create(PackageComment, PackageBase=package.PackageBase,
                            User=maintainer, Comments="Test",
                            RenderedComment=str(), CommentTS=now)

    cookies = {"AURSID": user.login(Request(), "testPassword")}
    pkgbasename = package.PackageBase.Name
    endpoint = f"/pkgbase/{pkgbasename}/comments/{comment.ID}/form"
    with client as request:
        resp = request.get(endpoint, cookies=cookies)
    assert resp.status_code == int(HTTPStatus.UNAUTHORIZED)


def test_pkgbase_comment_form_not_found(client: TestClient, maintainer: User,
                                        package: Package):
    cookies = {"AURSID": maintainer.login(Request(), "testPassword")}
    comment_id = 12345  # A non-existing comment.
    pkgbasename = package.PackageBase.Name
    endpoint = f"/pkgbase/{pkgbasename}/comments/{comment_id}/form"
    with client as request:
        resp = request.get(endpoint, cookies=cookies)
    assert resp.status_code == int(HTTPStatus.NOT_FOUND)


def test_pkgbase_comments_missing_comment(client: TestClient, maintainer: User,
                                          package: Package):
    cookies = {"AURSID": maintainer.login(Request(), "testPassword")}
    endpoint = f"/pkgbase/{package.PackageBase.Name}/comments"
    with client as request:
        resp = request.post(endpoint, cookies=cookies)
    assert resp.status_code == int(HTTPStatus.EXPECTATION_FAILED)


def test_pkgbase_comments(client: TestClient, maintainer: User, user: User,
                          package: Package):
    cookies = {"AURSID": maintainer.login(Request(), "testPassword")}
    pkgbasename = package.PackageBase.Name
    endpoint = f"/pkgbase/{pkgbasename}/comments"
    with client as request:
        resp = request.post(endpoint, data={
            "comment": "Test comment.",
            "enable_notifications": True
        }, cookies=cookies)
    assert resp.status_code == int(HTTPStatus.SEE_OTHER)

    expected_prefix = f"/pkgbase/{pkgbasename}"
    prefix_len = len(expected_prefix)
    assert resp.headers.get("location")[:prefix_len] == expected_prefix

    with client as request:
        resp = request.get(resp.headers.get("location"))
    assert resp.status_code == int(HTTPStatus.OK)

    root = parse_root(resp.text)
    headers = root.xpath('//h4[@class="comment-header"]')
    bodies = root.xpath('//div[@class="article-content"]/div/p')

    assert len(headers) == 1
    assert len(bodies) == 1

    assert bodies[0].text.strip() == "Test comment."

    # Clear up the PackageNotification. This doubles as testing
    # that the notification was created and clears it up so we can
    # test enabling it during edit.
    pkgbase = package.PackageBase
    db_notif = pkgbase.notifications.filter(
        PackageNotification.UserID == maintainer.ID
    ).first()
    with db.begin():
        db.session.delete(db_notif)

    # Now, let's edit the comment we just created.
    comment_id = int(headers[0].attrib["id"].split("-")[-1])
    endpoint = f"/pkgbase/{pkgbasename}/comments/{comment_id}"
    with client as request:
        resp = request.post(endpoint, data={
            "comment": "Edited comment.",
            "enable_notifications": True
        }, cookies=cookies)
    assert resp.status_code == int(HTTPStatus.SEE_OTHER)

    with client as request:
        resp = request.get(resp.headers.get("location"))
    assert resp.status_code == int(HTTPStatus.OK)

    root = parse_root(resp.text)
    headers = root.xpath('//h4[@class="comment-header"]')
    bodies = root.xpath('//div[@class="article-content"]/div/p')

    assert len(headers) == 1
    assert len(bodies) == 1

    assert bodies[0].text.strip() == "Edited comment."

    # Ensure that a notification was created.
    db_notif = pkgbase.notifications.filter(
        PackageNotification.UserID == maintainer.ID
    ).first()
    assert db_notif is not None

    # Don't supply a comment; should return EXPECTATION_FAILED.
    with client as request:
        fail_resp = request.post(endpoint, cookies=cookies)
    assert fail_resp.status_code == int(HTTPStatus.EXPECTATION_FAILED)

    # Now, test the form route, which should return form markup
    # via JSON.
    endpoint = f"{endpoint}/form"
    with client as request:
        resp = request.get(endpoint, cookies=cookies)
    assert resp.status_code == int(HTTPStatus.OK)

    data = resp.json()
    assert "form" in data


def test_pkgbase_comment_delete(client: TestClient,
                                maintainer: User,
                                user: User,
                                package: Package,
                                comment: PackageComment):
    # Test the unauthorized case of comment deletion.
    cookies = {"AURSID": user.login(Request(), "testPassword")}
    pkgbasename = package.PackageBase.Name
    endpoint = f"/pkgbase/{pkgbasename}/comments/{comment.ID}/delete"
    with client as request:
        resp = request.post(endpoint, cookies=cookies)
    assert resp.status_code == int(HTTPStatus.SEE_OTHER)

    expected = f"/pkgbase/{pkgbasename}"
    assert resp.headers.get("location") == expected

    # Test the unauthorized case of comment undeletion.
    maint_cookies = {"AURSID": maintainer.login(Request(), "testPassword")}
    endpoint = f"/pkgbase/{pkgbasename}/comments/{comment.ID}/undelete"
    with client as request:
        resp = request.post(endpoint, cookies=maint_cookies)
    assert resp.status_code == int(HTTPStatus.UNAUTHORIZED)

    # And move on to undeleting it.
    with client as request:
        resp = request.post(endpoint, cookies=cookies)
    assert resp.status_code == int(HTTPStatus.SEE_OTHER)


def test_pkgbase_comment_delete_unauthorized(client: TestClient,
                                             maintainer: User,
                                             package: Package,
                                             comment: PackageComment):
    # Test the unauthorized case of comment deletion.
    cookies = {"AURSID": maintainer.login(Request(), "testPassword")}
    pkgbasename = package.PackageBase.Name
    endpoint = f"/pkgbase/{pkgbasename}/comments/{comment.ID}/delete"
    with client as request:
        resp = request.post(endpoint, cookies=cookies)
    assert resp.status_code == int(HTTPStatus.UNAUTHORIZED)


def test_pkgbase_comment_delete_not_found(client: TestClient,
                                          maintainer: User,
                                          package: Package):
    cookies = {"AURSID": maintainer.login(Request(), "testPassword")}
    comment_id = 12345  # Non-existing comment.
    pkgbasename = package.PackageBase.Name
    endpoint = f"/pkgbase/{pkgbasename}/comments/{comment_id}/delete"
    with client as request:
        resp = request.post(endpoint, cookies=cookies)
    assert resp.status_code == int(HTTPStatus.NOT_FOUND)


def test_pkgbase_comment_undelete_not_found(client: TestClient,
                                            maintainer: User,
                                            package: Package):
    cookies = {"AURSID": maintainer.login(Request(), "testPassword")}
    comment_id = 12345  # Non-existing comment.
    pkgbasename = package.PackageBase.Name
    endpoint = f"/pkgbase/{pkgbasename}/comments/{comment_id}/undelete"
    with client as request:
        resp = request.post(endpoint, cookies=cookies)
    assert resp.status_code == int(HTTPStatus.NOT_FOUND)


def test_pkgbase_comment_pin(client: TestClient,
                             maintainer: User,
                             package: Package,
                             comment: PackageComment):
    cookies = {"AURSID": maintainer.login(Request(), "testPassword")}
    comment_id = comment.ID
    pkgbasename = package.PackageBase.Name

    # Pin the comment.
    endpoint = f"/pkgbase/{pkgbasename}/comments/{comment_id}/pin"
    with client as request:
        resp = request.post(endpoint, cookies=cookies)
    assert resp.status_code == int(HTTPStatus.SEE_OTHER)

    # Assert that PinnedTS got set.
    assert comment.PinnedTS > 0

    # Unpin the comment we just pinned.
    endpoint = f"/pkgbase/{pkgbasename}/comments/{comment_id}/unpin"
    with client as request:
        resp = request.post(endpoint, cookies=cookies)
    assert resp.status_code == int(HTTPStatus.SEE_OTHER)

    # Let's assert that PinnedTS was unset.
    assert comment.PinnedTS == 0


def test_pkgbase_comment_pin_unauthorized(client: TestClient,
                                          user: User,
                                          package: Package,
                                          comment: PackageComment):
    cookies = {"AURSID": user.login(Request(), "testPassword")}
    comment_id = comment.ID
    pkgbasename = package.PackageBase.Name
    endpoint = f"/pkgbase/{pkgbasename}/comments/{comment_id}/pin"
    with client as request:
        resp = request.post(endpoint, cookies=cookies)
    assert resp.status_code == int(HTTPStatus.UNAUTHORIZED)


def test_pkgbase_comment_unpin_unauthorized(client: TestClient,
                                            user: User,
                                            package: Package,
                                            comment: PackageComment):
    cookies = {"AURSID": user.login(Request(), "testPassword")}
    comment_id = comment.ID
    pkgbasename = package.PackageBase.Name
    endpoint = f"/pkgbase/{pkgbasename}/comments/{comment_id}/unpin"
    with client as request:
        resp = request.post(endpoint, cookies=cookies)
    assert resp.status_code == int(HTTPStatus.UNAUTHORIZED)


def test_pkgbase_comaintainers_not_found(client: TestClient, maintainer: User):
    cookies = {"AURSID": maintainer.login(Request(), "testPassword")}
    endpoint = "/pkgbase/fake/comaintainers"
    with client as request:
        resp = request.get(endpoint, cookies=cookies, allow_redirects=False)
    assert resp.status_code == int(HTTPStatus.NOT_FOUND)


def test_pkgbase_comaintainers_post_not_found(client: TestClient,
                                              maintainer: User):
    cookies = {"AURSID": maintainer.login(Request(), "testPassword")}
    endpoint = "/pkgbase/fake/comaintainers"
    with client as request:
        resp = request.post(endpoint, cookies=cookies, allow_redirects=False)
    assert resp.status_code == int(HTTPStatus.NOT_FOUND)


def test_pkgbase_comaintainers_unauthorized(client: TestClient, user: User,
                                            package: Package):
    pkgbase = package.PackageBase
    endpoint = f"/pkgbase/{pkgbase.Name}/comaintainers"
    cookies = {"AURSID": user.login(Request(), "testPassword")}
    with client as request:
        resp = request.get(endpoint, cookies=cookies, allow_redirects=False)
    assert resp.status_code == int(HTTPStatus.SEE_OTHER)
    assert resp.headers.get("location") == f"/pkgbase/{pkgbase.Name}"


def test_pkgbase_comaintainers_post_unauthorized(client: TestClient,
                                                 user: User,
                                                 package: Package):
    pkgbase = package.PackageBase
    endpoint = f"/pkgbase/{pkgbase.Name}/comaintainers"
    cookies = {"AURSID": user.login(Request(), "testPassword")}
    with client as request:
        resp = request.post(endpoint, cookies=cookies, allow_redirects=False)
    assert resp.status_code == int(HTTPStatus.SEE_OTHER)
    assert resp.headers.get("location") == f"/pkgbase/{pkgbase.Name}"


def test_pkgbase_comaintainers_post_invalid_user(client: TestClient,
                                                 maintainer: User,
                                                 package: Package):
    pkgbase = package.PackageBase
    endpoint = f"/pkgbase/{pkgbase.Name}/comaintainers"
    cookies = {"AURSID": maintainer.login(Request(), "testPassword")}
    with client as request:
        resp = request.post(endpoint, data={
            "users": "\nfake\n"
        }, cookies=cookies, allow_redirects=False)
    assert resp.status_code == int(HTTPStatus.OK)

    root = parse_root(resp.text)
    error = root.xpath('//ul[@class="errorlist"]/li')[0]
    assert error.text.strip() == "Invalid user name: fake"


def test_pkgbase_comaintainers(client: TestClient, user: User,
                               maintainer: User, package: Package):
    pkgbase = package.PackageBase
    endpoint = f"/pkgbase/{pkgbase.Name}/comaintainers"
    cookies = {"AURSID": maintainer.login(Request(), "testPassword")}

    # Start off by adding user as a comaintainer to package.
    # The maintainer username given should be ignored.
    with client as request:
        resp = request.post(endpoint, data={
            "users": f"\n{user.Username}\n{maintainer.Username}\n"
        }, cookies=cookies, allow_redirects=False)
    assert resp.status_code == int(HTTPStatus.SEE_OTHER)
    assert resp.headers.get("location") == f"/pkgbase/{pkgbase.Name}"

    # Do it again to exercise the last_priority bump path.
    with client as request:
        resp = request.post(endpoint, data={
            "users": f"\n{user.Username}\n{maintainer.Username}\n"
        }, cookies=cookies, allow_redirects=False)
    assert resp.status_code == int(HTTPStatus.SEE_OTHER)
    assert resp.headers.get("location") == f"/pkgbase/{pkgbase.Name}"

    # Now that we've added a comaintainer to the pkgbase,
    # let's perform a GET request to make sure that the backend produces
    # the user we added in the users textarea.
    with client as request:
        resp = request.get(endpoint, cookies=cookies, allow_redirects=False)
    assert resp.status_code == int(HTTPStatus.OK)

    root = parse_root(resp.text)
    users = root.xpath('//textarea[@id="id_users"]')[0]
    assert users.text.strip() == user.Username

    # Finish off by removing all the comaintainers.
    with client as request:
        resp = request.post(endpoint, data={
            "users": str()
        }, cookies=cookies, allow_redirects=False)
    assert resp.status_code == int(HTTPStatus.SEE_OTHER)
    assert resp.headers.get("location") == f"/pkgbase/{pkgbase.Name}"

    with client as request:
        resp = request.get(endpoint, cookies=cookies, allow_redirects=False)
    assert resp.status_code == int(HTTPStatus.OK)

    root = parse_root(resp.text)
    users = root.xpath('//textarea[@id="id_users"]')[0]
    assert users is not None and users.text is None


def test_requests_unauthorized(client: TestClient):
    with client as request:
        resp = request.get("/requests", allow_redirects=False)
    assert resp.status_code == int(HTTPStatus.SEE_OTHER)


def test_requests(client: TestClient,
                  maintainer: User,
                  tu_user: User,
                  packages: List[Package],
                  requests: List[PackageRequest]):
    cookies = {"AURSID": tu_user.login(Request(), "testPassword")}
    with client as request:
        resp = request.get("/requests", params={
            # Pass in url query parameters O, SeB and SB to exercise
            # their paths inside of the pager_nav used in this request.
            "O": 0,  # Page 1
            "SeB": "nd",
            "SB": "n"
        }, cookies=cookies)
    assert resp.status_code == int(HTTPStatus.OK)

    assert "Next ›" in resp.text
    assert "Last »" in resp.text

    root = parse_root(resp.text)
    # We have 55 requests, our defaults.PP is 50, so expect we have 50 rows.
    rows = root.xpath('//table[@class="results"]/tbody/tr')
    assert len(rows) == defaults.PP

    # Request page 2 of the requests page.
    with client as request:
        resp = request.get("/requests", params={
            "O": 50  # Page 2
        }, cookies=cookies)
    assert resp.status_code == int(HTTPStatus.OK)

    assert "‹ Previous" in resp.text
    assert "« First" in resp.text

    root = parse_root(resp.text)
    rows = root.xpath('//table[@class="results"]/tbody/tr')
    assert len(rows) == 5  # There are five records left on the second page.


def test_requests_selfmade(client: TestClient, user: User,
                           requests: List[PackageRequest]):
    cookies = {"AURSID": user.login(Request(), "testPassword")}
    with client as request:
        resp = request.get("/requests", cookies=cookies)
    assert resp.status_code == int(HTTPStatus.OK)

    # As the user who creates all of the requests, we should see all of them.
    # However, we are not allowed to accept any of them ourselves.
    root = parse_root(resp.text)
    rows = root.xpath('//table[@class="results"]/tbody/tr')
    assert len(rows) == defaults.PP

    # Our first and only link in the last row should be "Close".
    for row in rows:
        last_row = row.xpath('./td')[-1].xpath('./a')[0]
        assert last_row.text.strip() == "Close"


def test_pkgbase_request_not_found(client: TestClient, user: User):
    pkgbase_name = "fake"
    endpoint = f"/pkgbase/{pkgbase_name}/request"

    cookies = {"AURSID": user.login(Request(), "testPassword")}
    with client as request:
        resp = request.get(endpoint, cookies=cookies)
    assert resp.status_code == int(HTTPStatus.NOT_FOUND)


def test_pkgbase_request(client: TestClient, user: User, package: Package):
    pkgbase = package.PackageBase
    endpoint = f"/pkgbase/{pkgbase.Name}/request"

    cookies = {"AURSID": user.login(Request(), "testPassword")}
    with client as request:
        resp = request.get(endpoint, cookies=cookies)
    assert resp.status_code == int(HTTPStatus.OK)


def test_pkgbase_request_post_deletion(client: TestClient, user: User,
                                       package: Package):
    endpoint = f"/pkgbase/{package.PackageBase.Name}/request"
    cookies = {"AURSID": user.login(Request(), "testPassword")}
    with client as request:
        resp = request.post(endpoint, data={
            "type": "deletion",
            "comments": "We want to delete this."
        }, cookies=cookies, allow_redirects=False)
    assert resp.status_code == int(HTTPStatus.SEE_OTHER)

    pkgreq = db.query(PackageRequest).filter(
        PackageRequest.PackageBaseID == package.PackageBase.ID
    ).first()
    assert pkgreq is not None
    assert pkgreq.RequestType.Name == "deletion"
    assert pkgreq.PackageBaseName == package.PackageBase.Name
    assert pkgreq.Comments == "We want to delete this."


def test_pkgbase_request_post_orphan(client: TestClient, user: User,
                                     package: Package):
    endpoint = f"/pkgbase/{package.PackageBase.Name}/request"
    cookies = {"AURSID": user.login(Request(), "testPassword")}
    with client as request:
        resp = request.post(endpoint, data={
            "type": "orphan",
            "comments": "We want to disown this."
        }, cookies=cookies, allow_redirects=False)
    assert resp.status_code == int(HTTPStatus.SEE_OTHER)

    pkgreq = db.query(PackageRequest).filter(
        PackageRequest.PackageBaseID == package.PackageBase.ID
    ).first()
    assert pkgreq is not None
    assert pkgreq.RequestType.Name == "orphan"
    assert pkgreq.PackageBaseName == package.PackageBase.Name
    assert pkgreq.Comments == "We want to disown this."


def test_pkgbase_request_post_merge(client: TestClient, user: User,
                                    package: Package):
    with db.begin():
        pkgbase2 = db.create(PackageBase, Name="new-pkgbase",
                             Submitter=user, Maintainer=user, Packager=user)
        target = db.create(Package, PackageBase=pkgbase2,
                           Name=pkgbase2.Name, Version="1.0.0")

    endpoint = f"/pkgbase/{package.PackageBase.Name}/request"
    cookies = {"AURSID": user.login(Request(), "testPassword")}
    with client as request:
        resp = request.post(endpoint, data={
            "type": "merge",
            "merge_into": target.PackageBase.Name,
            "comments": "We want to merge this."
        }, cookies=cookies, allow_redirects=False)
    assert resp.status_code == int(HTTPStatus.SEE_OTHER)

    pkgreq = db.query(PackageRequest).filter(
        PackageRequest.PackageBaseID == package.PackageBase.ID
    ).first()
    assert pkgreq is not None
    assert pkgreq.RequestType.Name == "merge"
    assert pkgreq.PackageBaseName == package.PackageBase.Name
    assert pkgreq.MergeBaseName == target.PackageBase.Name
    assert pkgreq.Comments == "We want to merge this."


def test_pkgbase_request_post_not_found(client: TestClient, user: User):
    cookies = {"AURSID": user.login(Request(), "testPassword")}
    with client as request:
        resp = request.post("/pkgbase/fake/request", data={
            "type": "fake"
        }, cookies=cookies)
    assert resp.status_code == int(HTTPStatus.NOT_FOUND)


def test_pkgbase_request_post_invalid_type(client: TestClient,
                                           user: User,
                                           package: Package):
    endpoint = f"/pkgbase/{package.PackageBase.Name}/request"
    cookies = {"AURSID": user.login(Request(), "testPassword")}
    with client as request:
        resp = request.post(endpoint, data={"type": "fake"}, cookies=cookies)
    assert resp.status_code == int(HTTPStatus.BAD_REQUEST)


def test_pkgbase_request_post_no_comment_error(client: TestClient,
                                               user: User,
                                               package: Package):
    endpoint = f"/pkgbase/{package.PackageBase.Name}/request"
    cookies = {"AURSID": user.login(Request(), "testPassword")}
    with client as request:
        resp = request.post(endpoint, data={
            "type": "deletion",
            "comments": ""  # An empty comment field causes an error.
        }, cookies=cookies)
    assert resp.status_code == int(HTTPStatus.OK)

    root = parse_root(resp.text)
    error = root.xpath('//ul[@class="errorlist"]/li')[0]
    expected = "The comment field must not be empty."
    assert error.text.strip() == expected


def test_pkgbase_request_post_merge_not_found_error(client: TestClient,
                                                    user: User,
                                                    package: Package):
    endpoint = f"/pkgbase/{package.PackageBase.Name}/request"
    cookies = {"AURSID": user.login(Request(), "testPassword")}
    with client as request:
        resp = request.post(endpoint, data={
            "type": "merge",
            "merge_into": "fake",  # There is no PackageBase.Name "fake"
            "comments": "We want to merge this."
        }, cookies=cookies, allow_redirects=False)
    assert resp.status_code == int(HTTPStatus.OK)

    root = parse_root(resp.text)
    error = root.xpath('//ul[@class="errorlist"]/li')[0]
    expected = "The package base you want to merge into does not exist."
    assert error.text.strip() == expected


def test_pkgbase_request_post_merge_no_merge_into_error(client: TestClient,
                                                        user: User,
                                                        package: Package):
    endpoint = f"/pkgbase/{package.PackageBase.Name}/request"
    cookies = {"AURSID": user.login(Request(), "testPassword")}
    with client as request:
        resp = request.post(endpoint, data={
            "type": "merge",
            "merge_into": "",  # There is no PackageBase.Name "fake"
            "comments": "We want to merge this."
        }, cookies=cookies, allow_redirects=False)
    assert resp.status_code == int(HTTPStatus.OK)

    root = parse_root(resp.text)
    error = root.xpath('//ul[@class="errorlist"]/li')[0]
    expected = 'The "Merge into" field must not be empty.'
    assert error.text.strip() == expected


def test_pkgbase_request_post_merge_self_error(client: TestClient, user: User,
                                               package: Package):
    endpoint = f"/pkgbase/{package.PackageBase.Name}/request"
    cookies = {"AURSID": user.login(Request(), "testPassword")}
    with client as request:
        resp = request.post(endpoint, data={
            "type": "merge",
            "merge_into": package.PackageBase.Name,
            "comments": "We want to merge this."
        }, cookies=cookies, allow_redirects=False)
    assert resp.status_code == int(HTTPStatus.OK)

    root = parse_root(resp.text)
    error = root.xpath('//ul[@class="errorlist"]/li')[0]
    expected = "You cannot merge a package base into itself."
    assert error.text.strip() == expected


@pytest.fixture
def pkgreq(user: User, package: Package) -> PackageRequest:
    reqtype = db.query(RequestType).filter(
        RequestType.ID == DELETION_ID
    ).first()
    with db.begin():
        pkgreq = db.create(PackageRequest,
                           RequestType=reqtype,
                           User=user,
                           PackageBase=package.PackageBase,
                           PackageBaseName=package.PackageBase.Name,
                           Comments=str(),
                           ClosureComment=str())
    yield pkgreq


def test_requests_close(client: TestClient, user: User,
                        pkgreq: PackageRequest):
    cookies = {"AURSID": user.login(Request(), "testPassword")}
    with client as request:
        resp = request.get(f"/requests/{pkgreq.ID}/close", cookies=cookies,
                           allow_redirects=False)
    assert resp.status_code == int(HTTPStatus.OK)


def test_requests_close_unauthorized(client: TestClient, maintainer: User,
                                     pkgreq: PackageRequest):
    cookies = {"AURSID": maintainer.login(Request(), "testPassword")}
    with client as request:
        resp = request.get(f"/requests/{pkgreq.ID}/close", cookies=cookies,
                           allow_redirects=False)
    assert resp.status_code == int(HTTPStatus.SEE_OTHER)
    assert resp.headers.get("location") == "/"


def test_requests_close_post_invalid_reason(client: TestClient, user: User,
                                            pkgreq: PackageRequest):
    cookies = {"AURSID": user.login(Request(), "testPassword")}
    with client as request:
        resp = request.post(f"/requests/{pkgreq.ID}/close", data={
            "reason": 0
        }, cookies=cookies, allow_redirects=False)
    assert resp.status_code == int(HTTPStatus.BAD_REQUEST)


def test_requests_close_post_unauthorized(client: TestClient, maintainer: User,
                                          pkgreq: PackageRequest):
    cookies = {"AURSID": maintainer.login(Request(), "testPassword")}
    with client as request:
        resp = request.post(f"/requests/{pkgreq.ID}/close", data={
            "reason": ACCEPTED_ID
        }, cookies=cookies, allow_redirects=False)
    assert resp.status_code == int(HTTPStatus.SEE_OTHER)
    assert resp.headers.get("location") == "/"


def test_requests_close_post(client: TestClient, user: User,
                             pkgreq: PackageRequest):
    cookies = {"AURSID": user.login(Request(), "testPassword")}
    with client as request:
        resp = request.post(f"/requests/{pkgreq.ID}/close", data={
            "reason": REJECTED_ID
        }, cookies=cookies, allow_redirects=False)
    assert resp.status_code == int(HTTPStatus.SEE_OTHER)

    assert pkgreq.Status == REJECTED_ID
    assert pkgreq.Closer == user
    assert pkgreq.ClosureComment == str()


def test_requests_close_post_rejected(client: TestClient, user: User,
                                      pkgreq: PackageRequest):
    cookies = {"AURSID": user.login(Request(), "testPassword")}
    with client as request:
        resp = request.post(f"/requests/{pkgreq.ID}/close", data={
            "reason": REJECTED_ID
        }, cookies=cookies, allow_redirects=False)
    assert resp.status_code == int(HTTPStatus.SEE_OTHER)

    assert pkgreq.Status == REJECTED_ID
    assert pkgreq.Closer == user
    assert pkgreq.ClosureComment == str()
