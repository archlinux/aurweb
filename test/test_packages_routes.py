import re
from http import HTTPStatus
from unittest import mock

import pytest
from fastapi.testclient import TestClient

from aurweb import asgi, cache, config, db, time
from aurweb.filters import datetime_display
from aurweb.models import License, PackageLicense
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
from aurweb.models.package_request import PackageRequest
from aurweb.models.package_vote import PackageVote
from aurweb.models.relation_type import (
    CONFLICTS_ID,
    PROVIDES_ID,
    REPLACES_ID,
    RelationType,
)
from aurweb.models.request_type import DELETION_ID, RequestType
from aurweb.models.user import User
from aurweb.testing.html import get_errors, get_successes, parse_root
from aurweb.testing.requests import Request


def package_endpoint(package: Package) -> str:
    return f"/packages/{package.Name}"


def create_package(pkgname: str, maintainer: User) -> Package:
    pkgbase = db.create(PackageBase, Name=pkgname, Maintainer=maintainer)
    return db.create(Package, Name=pkgbase.Name, PackageBase=pkgbase)


def create_package_dep(
    package: Package, depname: str, dep_type_name: str = "depends"
) -> PackageDependency:
    dep_type = db.query(DependencyType, DependencyType.Name == dep_type_name).first()
    return db.create(
        PackageDependency, DependencyType=dep_type, Package=package, DepName=depname
    )


def create_package_rel(package: Package, relname: str) -> PackageRelation:
    rel_type = db.query(RelationType, RelationType.ID == PROVIDES_ID).first()
    return db.create(
        PackageRelation, RelationType=rel_type, Package=package, RelName=relname
    )


@pytest.fixture(autouse=True)
def setup(db_test):
    return


@pytest.fixture(autouse=True)
def clear_fakeredis_cache():
    cache._redis.flushall()


@pytest.fixture
def client() -> TestClient:
    """Yield a FastAPI TestClient."""
    client = TestClient(app=asgi.app)

    # disable redirects for our tests
    client.follow_redirects = False
    yield client


def create_user(username: str) -> User:
    with db.begin():
        user = db.create(
            User,
            Username=username,
            Email=f"{username}@example.org",
            Passwd="testPassword",
            AccountTypeID=USER_ID,
        )
    return user


@pytest.fixture
def user() -> User:
    """Yield a user."""
    user = create_user("test")
    yield user


@pytest.fixture
def maintainer() -> User:
    """Yield a specific User used to maintain packages."""
    account_type = db.query(AccountType, AccountType.ID == USER_ID).first()
    with db.begin():
        maintainer = db.create(
            User,
            Username="test_maintainer",
            Email="test_maintainer@example.org",
            Passwd="testPassword",
            AccountType=account_type,
        )
    yield maintainer


@pytest.fixture
def pm_user():
    pm_type = db.query(
        AccountType, AccountType.AccountType == "Package Maintainer"
    ).first()
    with db.begin():
        pm_user = db.create(
            User,
            Username="test_pm",
            Email="test_pm@example.org",
            RealName="Test PM",
            Passwd="testPassword",
            AccountType=pm_type,
        )
    yield pm_user


@pytest.fixture
def user_who_hates_grey_comments() -> User:
    """Yield a specific User who doesn't like grey comments."""
    account_type = db.query(AccountType, AccountType.ID == USER_ID).first()
    with db.begin():
        user_who_hates_grey_comments = db.create(
            User,
            Username="test_hater",
            Email="test_hater@example.org",
            Passwd="testPassword",
            AccountType=account_type,
            HideDeletedComments=True,
        )
    yield user_who_hates_grey_comments


@pytest.fixture
def package(maintainer: User) -> Package:
    """Yield a Package created by user."""
    now = time.utcnow()
    with db.begin():
        pkgbase = db.create(
            PackageBase,
            Name="test-package",
            Maintainer=maintainer,
            Packager=maintainer,
            Submitter=maintainer,
            ModifiedTS=now,
        )
        package = db.create(Package, PackageBase=pkgbase, Name=pkgbase.Name)
    yield package


@pytest.fixture
def pkgbase(package: Package) -> PackageBase:
    yield package.PackageBase


@pytest.fixture
def target(maintainer: User) -> PackageBase:
    """Merge target."""
    now = time.utcnow()
    with db.begin():
        pkgbase = db.create(
            PackageBase,
            Name="target-package",
            Maintainer=maintainer,
            Packager=maintainer,
            Submitter=maintainer,
            ModifiedTS=now,
        )
        db.create(Package, PackageBase=pkgbase, Name=pkgbase.Name)
    yield pkgbase


@pytest.fixture
def pkgreq(user: User, pkgbase: PackageBase) -> PackageRequest:
    """Yield a PackageRequest related to `pkgbase`."""
    with db.begin():
        pkgreq = db.create(
            PackageRequest,
            ReqTypeID=DELETION_ID,
            User=user,
            PackageBase=pkgbase,
            PackageBaseName=pkgbase.Name,
            Comments=f"Deletion request for {pkgbase.Name}",
            ClosureComment=str(),
        )
    yield pkgreq


@pytest.fixture
def comment(user: User, package: Package) -> PackageComment:
    pkgbase = package.PackageBase
    now = time.utcnow()
    with db.begin():
        comment = db.create(
            PackageComment,
            User=user,
            PackageBase=pkgbase,
            Comments="Test comment.",
            RenderedComment=str(),
            CommentTS=now,
        )
    yield comment


@pytest.fixture
def deleted_comment(user: User, package: Package) -> PackageComment:
    pkgbase = package.PackageBase
    now = time.utcnow()
    with db.begin():
        comment = db.create(
            PackageComment,
            User=user,
            PackageBase=pkgbase,
            Comments="Test comment.",
            RenderedComment=str(),
            CommentTS=now,
            DelTS=now,
        )
    yield comment


@pytest.fixture
def packages(maintainer: User) -> list[Package]:
    """Yield 55 packages named pkg_0 .. pkg_54."""
    packages_ = []
    now = time.utcnow()
    with db.begin():
        for i in range(55):
            pkgbase = db.create(
                PackageBase,
                Name=f"pkg_{i}",
                Maintainer=maintainer,
                Packager=maintainer,
                Submitter=maintainer,
                ModifiedTS=now,
            )
            package = db.create(Package, PackageBase=pkgbase, Name=f"pkg_{i}")
            packages_.append(package)

    yield packages_


def test_package_not_found(client: TestClient):
    with client as request:
        resp = request.get("/packages/not_found")
    assert resp.status_code == int(HTTPStatus.NOT_FOUND)


def test_package(client: TestClient, package: Package):
    """Test a single / packages / {name} route."""

    with db.begin():
        db.create(
            PackageRelation,
            PackageID=package.ID,
            RelTypeID=PROVIDES_ID,
            RelName="test_provider1",
        )
        db.create(
            PackageRelation,
            PackageID=package.ID,
            RelTypeID=PROVIDES_ID,
            RelName="test_provider2",
        )

        db.create(
            PackageRelation,
            PackageID=package.ID,
            RelTypeID=REPLACES_ID,
            RelName="test_replacer1",
        )
        db.create(
            PackageRelation,
            PackageID=package.ID,
            RelTypeID=REPLACES_ID,
            RelName="test_replacer2",
        )

        db.create(
            PackageRelation,
            PackageID=package.ID,
            RelTypeID=CONFLICTS_ID,
            RelName="test_conflict1",
        )
        db.create(
            PackageRelation,
            PackageID=package.ID,
            RelTypeID=CONFLICTS_ID,
            RelName="test_conflict2",
        )

        # Create some licenses.
        licenses = [
            db.create(License, Name="test_license1"),
            db.create(License, Name="test_license2"),
        ]

        db.create(PackageLicense, PackageID=package.ID, License=licenses[0])
        db.create(PackageLicense, PackageID=package.ID, License=licenses[1])

        # Create some keywords
        keywords = ["test1", "test2"]
        for keyword in keywords:
            db.create(
                PackageKeyword, PackageBaseID=package.PackageBaseID, Keyword=keyword
            )

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

    licenses = root.xpath('//tr[@id="licenses"]/td')
    expected = ["test_license1", "test_license2"]
    assert licenses[0].text.strip() == ", ".join(expected)

    provides = root.xpath('//tr[@id="provides"]/td')
    expected = ["test_provider1", "test_provider2"]
    assert provides[0].text.strip() == ", ".join(expected)

    replaces = root.xpath('//tr[@id="replaces"]/td')
    expected = ["test_replacer1", "test_replacer2"]
    assert replaces[0].text.strip() == ", ".join(expected)

    conflicts = root.xpath('//tr[@id="conflicts"]/td')
    expected = ["test_conflict1", "test_conflict2"]
    assert conflicts[0].text.strip() == ", ".join(expected)

    keywords = root.xpath('//a[@class="keyword"]')
    expected = ["test1", "test2"]
    for i, keyword in enumerate(expected):
        assert keywords[i].text.strip() == keyword


def test_package_split_description(client: TestClient, user: User):
    with db.begin():
        pkgbase = db.create(
            PackageBase,
            Name="pkgbase",
            Maintainer=user,
            Packager=user,
        )

        pkg_a = db.create(
            Package,
            PackageBase=pkgbase,
            Name="pkg_a",
            Description="pkg_a desc",
        )
        pkg_b = db.create(
            Package,
            PackageBase=pkgbase,
            Name="pkg_b",
            Description="pkg_b desc",
        )

    # Check pkg_a
    with client as request:
        endp = f"/packages/{pkg_a.Name}"
        resp = request.get(endp)
    assert resp.status_code == HTTPStatus.OK

    root = parse_root(resp.text)
    row = root.xpath('//tr[@id="pkg-description"]/td')[0]
    assert row.text == pkg_a.Description

    # Check pkg_b
    with client as request:
        endp = f"/packages/{pkg_b.Name}"
        resp = request.get(endp)
    assert resp.status_code == HTTPStatus.OK

    root = parse_root(resp.text)
    row = root.xpath('//tr[@id="pkg-description"]/td')[0]
    assert row.text == pkg_b.Description


def test_paged_depends_required(client: TestClient, package: Package):
    maint = package.PackageBase.Maintainer
    new_pkgs = []

    with db.begin():
        # Create 25 new packages that'll be used to depend on our package.
        for i in range(26):
            base = db.create(PackageBase, Name=f"new_pkg{i}", Maintainer=maint)
            new_pkgs.append(db.create(Package, Name=base.Name, PackageBase=base))

        # Create 25 deps.
        for i in range(25):
            create_package_dep(package, f"dep_{i}")

    with db.begin():
        # Create depends on this package so we get some required by listings.
        for new_pkg in new_pkgs:
            create_package_dep(new_pkg, package.Name)

    with client as request:
        resp = request.get(package_endpoint(package))
    assert resp.status_code == int(HTTPStatus.OK)

    # Test depends show link.
    assert "Show 5 more" in resp.text

    # Test required by show more link, we added 26 packages.
    assert "Show 6 more" in resp.text

    # Follow both links at the same time.
    with client as request:
        resp = request.get(
            package_endpoint(package),
            params={
                "all_deps": True,
                "all_reqs": True,
            },
        )
    assert resp.status_code == int(HTTPStatus.OK)

    # We're should see everything and have no link.
    assert "Show 5 more" not in resp.text
    assert "Show 6 more" not in resp.text


def test_package_comments(
    client: TestClient, user: User, user_who_hates_grey_comments: User, package: Package
):
    now = time.utcnow()
    with db.begin():
        comment = db.create(
            PackageComment,
            PackageBase=package.PackageBase,
            User=user,
            Comments="Test comment",
            CommentTS=now,
        )
        deleted_comment = db.create(
            PackageComment,
            PackageBase=package.PackageBase,
            User=user,
            Comments="Deleted Test comment",
            CommentTS=now,
            DelTS=now - 1,
        )

    cookies = {"AURSID": user.login(Request(), "testPassword")}
    with client as request:
        request.cookies = cookies
        resp = request.get(package_endpoint(package))
    assert resp.status_code == int(HTTPStatus.OK)

    root = parse_root(resp.text)
    expected = [comment.Comments, deleted_comment.Comments]
    comments = root.xpath(
        './/div[contains(@class, "package-comments")]'
        '/div[@class="article-content"]/div/text()'
    )
    assert len(comments) == 2
    for i, row in enumerate(expected):
        assert comments[i].strip() == row

    cookies = {"AURSID": user_who_hates_grey_comments.login(Request(), "testPassword")}
    with client as request:
        request.cookies = cookies
        resp = request.get(package_endpoint(package))
    assert resp.status_code == int(HTTPStatus.OK)

    root = parse_root(resp.text)
    expected = [comment.Comments]
    comments = root.xpath(
        './/div[contains(@class, "package-comments")]'
        '/div[@class="article-content"]/div/text()'
    )
    assert len(comments) == 1  # Deleted comment is hidden
    for i, row in enumerate(expected):
        assert comments[i].strip() == row


def test_package_requests_display(
    client: TestClient, user: User, package: Package, pkgreq: PackageRequest
):
    # Test that a single request displays "1 pending request".
    cookies = {"AURSID": user.login(Request(), "testPassword")}
    with client as request:
        request.cookies = cookies
        resp = request.get(package_endpoint(package))
    assert resp.status_code == int(HTTPStatus.OK)

    root = parse_root(resp.text)
    selector = '//div[@id="actionlist"]/ul/li/span[@class="flagged"]'
    target = root.xpath(selector)[0]
    assert target.text.strip() == "1 pending request"

    type_ = db.query(RequestType, RequestType.ID == DELETION_ID).first()
    with db.begin():
        db.create(
            PackageRequest,
            PackageBase=package.PackageBase,
            PackageBaseName=package.PackageBase.Name,
            User=user,
            RequestType=type_,
            Comments="Test comment2.",
            ClosureComment=str(),
        )

    # Test that a two requests display "2 pending requests".
    with client as request:
        request.cookies = cookies
        resp = request.get(package_endpoint(package))
    assert resp.status_code == int(HTTPStatus.OK)

    root = parse_root(resp.text)
    selector = '//div[@id="actionlist"]/ul/li/span[@class="flagged"]'
    target = root.xpath(selector)[0]
    assert target.text.strip() == "2 pending requests"


def test_package_authenticated(client: TestClient, user: User, package: Package):
    """We get the same here for either authenticated or not
    authenticated. Form inputs are presented to maintainers.
    This process also occurs when pkgbase.html is rendered."""
    cookies = {"AURSID": user.login(Request(), "testPassword")}
    with client as request:
        request.cookies = cookies
        resp = request.get(package_endpoint(package))
    assert resp.status_code == int(HTTPStatus.OK)

    expected = [
        "View PKGBUILD",
        "View Changes",
        "Download snapshot",
        "Search wiki",
        "Flag package out-of-date",
        "Vote for this package",
        "Enable notifications",
        "Submit Request",
    ]
    for expected_text in expected:
        assert expected_text in resp.text

    # make sure we don't have these. Only for Maintainer/TUs/Devs
    not_expected = [
        "Disown Package",
        "View Requests",
        "Delete Package",
        "Merge Package",
    ]
    for unexpected_text in not_expected:
        assert unexpected_text not in resp.text

    # When no requests are up, make sure we don't see the display for them.
    root = parse_root(resp.text)
    selector = '//div[@id="actionlist"]/ul/li/span[@class="flagged"]'
    target = root.xpath(selector)
    assert len(target) == 0


def test_package_authenticated_maintainer(
    client: TestClient, maintainer: User, package: Package
):
    cookies = {"AURSID": maintainer.login(Request(), "testPassword")}
    with client as request:
        request.cookies = cookies
        resp = request.get(package_endpoint(package))
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
        "Disown Package",
    ]
    for expected_text in expected:
        assert expected_text in resp.text

    # make sure we don't have these. Only for PMs/Devs
    not_expected = [
        "1 pending request",
        "Delete Package",
        "Merge Package",
    ]
    for unexpected_text in not_expected:
        assert unexpected_text not in resp.text


def test_package_authenticated_pm(
    client: TestClient, pm_user: User, package: Package, pkgreq: PackageRequest
):
    cookies = {"AURSID": pm_user.login(Request(), "testPassword")}
    with client as request:
        request.cookies = cookies
        resp = request.get(package_endpoint(package))
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
        "1 pending request",
        "Submit Request",
        "Delete Package",
        "Merge Package",
        "Disown Package",
    ]
    for expected_text in expected:
        assert expected_text in resp.text


def test_package_dependencies(client: TestClient, maintainer: User, package: Package):
    # Create a normal dependency of type depends.
    with db.begin():
        dep_pkg = create_package("test-dep-1", maintainer)
        dep = create_package_dep(package, dep_pkg.Name)

        # Also, create a makedepends.
        make_dep_pkg = create_package("test-dep-2", maintainer)
        make_dep = create_package_dep(
            package, make_dep_pkg.Name, dep_type_name="makedepends"
        )
        make_dep.DepArch = "x86_64"

        # And... a checkdepends!
        check_dep_pkg = create_package("test-dep-3", maintainer)
        create_package_dep(package, check_dep_pkg.Name, dep_type_name="checkdepends")

        # Geez. Just stop. This is optdepends.
        opt_dep_pkg = create_package("test-dep-4", maintainer)
        create_package_dep(package, opt_dep_pkg.Name, dep_type_name="optdepends")

        # Heh. Another optdepends to test one with a description.
        opt_desc_dep_pkg = create_package("test-dep-5", maintainer)
        opt_desc_dep = create_package_dep(
            package, opt_desc_dep_pkg.Name, dep_type_name="optdepends"
        )
        opt_desc_dep.DepDesc = "Test description."

        broken_dep = create_package_dep(package, "test-dep-6", dep_type_name="depends")

        # Create an official provider record.
        db.create(
            OfficialProvider, Name="test-dep-99", Repo="core", Provides="test-dep-99"
        )
        create_package_dep(package, "test-dep-99")

        # Also, create a provider who provides our test-dep-99.
        provider = create_package("test-provider", maintainer)
        create_package_rel(provider, dep.DepName)

    with client as request:
        resp = request.get(package_endpoint(package))
    assert resp.status_code == int(HTTPStatus.OK)

    # Let's make sure all the non-broken deps are ordered as we expect.
    expected = list(
        filter(
            lambda e: e.is_package(),
            package.package_dependencies.order_by(
                PackageDependency.DepTypeID.asc(), PackageDependency.DepName.asc()
            ).all(),
        )
    )
    root = parse_root(resp.text)
    pkgdeps = root.findall('.//ul[@id="pkgdepslist"]/li/a')
    for i, expectation in enumerate(expected):
        assert pkgdeps[i].text.strip() == expectation.DepName

    # Let's make sure the DepArch was displayed for our target make dep.
    arch = root.findall('.//ul[@id="pkgdepslist"]/li')[3]
    arch = arch.xpath("./em")[0]
    assert arch.text.strip() == "(make, x86_64)"

    # And let's make sure that the broken package was displayed.
    broken_node = root.find('.//ul[@id="pkgdepslist"]/li/span')
    assert broken_node.text.strip() == broken_dep.DepName


def test_packages(client: TestClient, packages: list[Package]):
    with client as request:
        response = request.get(
            "/packages",
            params={
                "SeB": "X",  # "X" isn't valid, defaults to "nd"
                "PP": "1 or 1",
                "O": "0 or 0",
            },
        )
    assert response.status_code == int(HTTPStatus.OK)

    root = parse_root(response.text)
    stats = root.xpath('//div[@class="pkglist-stats"]/p')[0]
    pager_text = re.sub(r"\s+", " ", stats.text.replace("\n", "").strip())
    assert pager_text == "55 packages found. Page 1 of 2."

    rows = root.xpath('//table[@class="results"]/tbody/tr')
    assert len(rows) == 50  # Default per-page


def test_packages_empty(client: TestClient):
    with client as request:
        response = request.get("/packages")
    assert response.status_code == int(HTTPStatus.OK)

    root = parse_root(response.text)
    results = root.xpath('//div[@id="pkglist-results"]/p')
    expected = "No packages matched your search criteria."
    assert results[0].text.strip() == expected


def test_packages_search_by_name(client: TestClient, packages: list[Package]):
    for keyword in ["pkg_", "PkG_"]:
        with client as request:
            response = request.get("/packages", params={"SeB": "n", "K": keyword})
        assert response.status_code == int(HTTPStatus.OK)

        root = parse_root(response.text)

        rows = root.xpath('//table[@class="results"]/tbody/tr')
        assert len(rows) == 50  # Default per-page


def test_packages_search_by_exact_name(client: TestClient, packages: list[Package]):
    with client as request:
        response = request.get("/packages", params={"SeB": "N", "K": "pkg_"})
    assert response.status_code == int(HTTPStatus.OK)

    root = parse_root(response.text)
    rows = root.xpath('//table[@class="results"]/tbody/tr')

    # There is no package named exactly 'pkg_', we get 0 results.
    assert len(rows) == 0

    for keyword in ["pkg_1", "PkG_1"]:
        with client as request:
            response = request.get("/packages", params={"SeB": "N", "K": keyword})
        assert response.status_code == int(HTTPStatus.OK)

        root = parse_root(response.text)
        rows = root.xpath('//table[@class="results"]/tbody/tr')

        # There's just one package named 'pkg_1', we get 1 result.
        assert len(rows) == 1


def test_packages_search_by_pkgbase(client: TestClient, packages: list[Package]):
    for keyword in ["pkg_", "PkG_"]:
        with client as request:
            response = request.get("/packages", params={"SeB": "b", "K": "pkg_"})
        assert response.status_code == int(HTTPStatus.OK)

        root = parse_root(response.text)

        rows = root.xpath('//table[@class="results"]/tbody/tr')
        assert len(rows) == 50


def test_packages_search_by_exact_pkgbase(client: TestClient, packages: list[Package]):
    with client as request:
        response = request.get("/packages", params={"SeB": "B", "K": "pkg_"})
    assert response.status_code == int(HTTPStatus.OK)

    root = parse_root(response.text)
    rows = root.xpath('//table[@class="results"]/tbody/tr')
    assert len(rows) == 0

    for keyword in ["pkg_1", "PkG_1"]:
        with client as request:
            response = request.get("/packages", params={"SeB": "B", "K": "pkg_1"})
        assert response.status_code == int(HTTPStatus.OK)

        root = parse_root(response.text)
        rows = root.xpath('//table[@class="results"]/tbody/tr')
        assert len(rows) == 1


def test_packages_search_by_keywords(client: TestClient, packages: list[Package]):
    # None of our packages have keywords, so this query should return nothing.
    with client as request:
        response = request.get("/packages", params={"SeB": "k", "K": "testKeyword"})
    assert response.status_code == int(HTTPStatus.OK)

    root = parse_root(response.text)
    rows = root.xpath('//table[@class="results"]/tbody/tr')
    assert len(rows) == 0

    # But now, let's create the keyword for the first package.
    package = packages[0]
    with db.begin():
        db.create(
            PackageKeyword, PackageBase=package.PackageBase, Keyword="testKeyword"
        )

    # And request packages with that keyword, we should get 1 result.
    for keyword in ["testkeyword", "TestKeyWord"]:
        with client as request:
            # clear fakeredis cache
            cache._redis.flushall()
            response = request.get("/packages", params={"SeB": "k", "K": keyword})
        assert response.status_code == int(HTTPStatus.OK)

        root = parse_root(response.text)
        rows = root.xpath('//table[@class="results"]/tbody/tr')
        assert len(rows) == 1

    # Now let's add another keyword to the same package
    with db.begin():
        db.create(
            PackageKeyword, PackageBase=package.PackageBase, Keyword="testKeyword2"
        )

    # And request packages with both keywords, we should still get 1 result.
    with client as request:
        response = request.get(
            "/packages", params={"SeB": "k", "K": "testKeyword testKeyword2"}
        )
    assert response.status_code == int(HTTPStatus.OK)

    root = parse_root(response.text)
    rows = root.xpath('//table[@class="results"]/tbody/tr')
    assert len(rows) == 1


def test_packages_search_by_maintainer(
    client: TestClient, maintainer: User, package: Package
):
    # We should expect that searching by `package`'s maintainer
    # returns `package` in the results.
    for keyword in [maintainer.Username, maintainer.Username.upper()]:
        with client as request:
            response = request.get("/packages", params={"SeB": "m", "K": keyword})
        assert response.status_code == int(HTTPStatus.OK)
        root = parse_root(response.text)
        rows = root.xpath('//table[@class="results"]/tbody/tr')
        assert len(rows) == 1

    # Search again by maintainer with no keywords given.
    # This kind of search returns all orphans instead.
    # In this first case, there are no orphan packages; assert that.
    with client as request:
        response = request.get("/packages", params={"SeB": "m"})
    assert response.status_code == int(HTTPStatus.OK)
    root = parse_root(response.text)
    rows = root.xpath('//table[@class="results"]/tbody/tr')
    assert len(rows) == 0

    # Orphan `package`.
    with db.begin():
        package.PackageBase.Maintainer = None

    # This time, we should get `package` returned, since it's now an orphan.
    with client as request:
        # clear fakeredis cache
        cache._redis.flushall()
        response = request.get("/packages", params={"SeB": "m"})
    assert response.status_code == int(HTTPStatus.OK)
    root = parse_root(response.text)
    rows = root.xpath('//table[@class="results"]/tbody/tr')
    assert len(rows) == 1


def test_packages_search_by_comaintainer(
    client: TestClient, maintainer: User, package: Package
):
    # Nobody's a comaintainer yet.
    with client as request:
        response = request.get(
            "/packages", params={"SeB": "c", "K": maintainer.Username}
        )
    assert response.status_code == int(HTTPStatus.OK)

    root = parse_root(response.text)
    rows = root.xpath('//table[@class="results"]/tbody/tr')
    assert len(rows) == 0

    # Now, we create a comaintainer.
    with db.begin():
        db.create(
            PackageComaintainer,
            PackageBase=package.PackageBase,
            User=maintainer,
            Priority=1,
        )

    # Then test that it's returned by our search.
    for keyword in [maintainer.Username, maintainer.Username.upper()]:
        with client as request:
            # clear fakeredis cache
            cache._redis.flushall()
            response = request.get("/packages", params={"SeB": "c", "K": keyword})
        assert response.status_code == int(HTTPStatus.OK)

        root = parse_root(response.text)
        rows = root.xpath('//table[@class="results"]/tbody/tr')
        assert len(rows) == 1


def test_packages_search_by_co_or_maintainer(
    client: TestClient, maintainer: User, package: Package
):
    with client as request:
        response = request.get(
            "/packages",
            params={
                "SeB": "M",
                "SB": "BLAH",  # Invalid SB; gets reset to default "n".
                "K": maintainer.Username,
            },
        )
    assert response.status_code == int(HTTPStatus.OK)

    root = parse_root(response.text)
    rows = root.xpath('//table[@class="results"]/tbody/tr')
    assert len(rows) == 1

    with db.begin():
        user = db.create(
            User,
            Username="comaintainer",
            Email="comaintainer@example.org",
            Passwd="testPassword",
        )
        db.create(
            PackageComaintainer, PackageBase=package.PackageBase, User=user, Priority=1
        )

    for keyword in [user.Username, user.Username.upper()]:
        with client as request:
            response = request.get("/packages", params={"SeB": "M", "K": keyword})
        assert response.status_code == int(HTTPStatus.OK)

        root = parse_root(response.text)
        rows = root.xpath('//table[@class="results"]/tbody/tr')
        assert len(rows) == 1


def test_packages_search_by_submitter(
    client: TestClient, maintainer: User, package: Package
):
    for keyword in [maintainer.Username, maintainer.Username.upper()]:
        with client as request:
            response = request.get("/packages", params={"SeB": "s", "K": keyword})
        assert response.status_code == int(HTTPStatus.OK)

        root = parse_root(response.text)
        rows = root.xpath('//table[@class="results"]/tbody/tr')
        assert len(rows) == 1


def test_packages_sort_by_name(client: TestClient, packages: list[Package]):
    with client as request:
        response = request.get(
            "/packages", params={"SB": "n", "SO": "a", "PP": "150"}  # Name  # Ascending
        )
    assert response.status_code == int(HTTPStatus.OK)

    root = parse_root(response.text)
    rows = root.xpath('//table[@class="results"]/tbody/tr')
    rows = [row.xpath("./td/a")[0].text.strip() for row in rows]

    with client as request:
        response2 = request.get(
            "/packages", params={"SB": "n", "SO": "d", "PP": "150"}  # Name  # Ascending
        )
    assert response2.status_code == int(HTTPStatus.OK)

    root = parse_root(response2.text)
    rows2 = root.xpath('//table[@class="results"]/tbody/tr')
    rows2 = [row.xpath("./td/a")[0].text.strip() for row in rows2]
    assert rows == list(reversed(rows2))


def test_packages_sort_by_votes(
    client: TestClient, maintainer: User, packages: list[Package]
):
    # Set the first package's NumVotes to 1.
    with db.begin():
        packages[0].PackageBase.NumVotes = 1

    # Test that, by default, the first result is what we just set above.
    with client as request:
        response = request.get("/packages", params={"SB": "v"})  # Votes.
    assert response.status_code == int(HTTPStatus.OK)

    root = parse_root(response.text)
    rows = root.xpath('//table[@class="results"]/tbody/tr')
    votes = rows[0].xpath("./td")[2]  # The third column of the first row.
    assert votes.text.strip() == "1"

    # Now, test that with an ascending order, the last result is
    # the one we set, since the default (above) is descending.
    with client as request:
        response = request.get(
            "/packages",
            params={
                "SB": "v",  # Votes.
                "SO": "a",  # Ascending.
                "O": "50",  # Second page.
            },
        )
    assert response.status_code == int(HTTPStatus.OK)

    root = parse_root(response.text)
    rows = root.xpath('//table[@class="results"]/tbody/tr')
    votes = rows[-1].xpath("./td")[2]  # The third column of the last row.
    assert votes.text.strip() == "1"


def test_packages_sort_by_popularity(
    client: TestClient, maintainer: User, packages: list[Package]
):
    # Set the first package's Popularity to 0.50.
    with db.begin():
        packages[0].PackageBase.Popularity = "0.50"

    # Test that, by default, the first result is what we just set above.
    with client as request:
        response = request.get("/packages", params={"SB": "p"})  # Popularity
    assert response.status_code == int(HTTPStatus.OK)

    root = parse_root(response.text)
    rows = root.xpath('//table[@class="results"]/tbody/tr')
    pop = rows[0].xpath("./td")[3]  # The fourth column of the first row.
    assert pop.text.strip() == "0.50"


def test_packages_sort_by_voted(
    client: TestClient, maintainer: User, packages: list[Package]
):
    now = time.utcnow()
    with db.begin():
        db.create(
            PackageVote,
            PackageBase=packages[0].PackageBase,
            User=maintainer,
            VoteTS=now,
        )

    # Test that, by default, the first result is what we just set above.
    cookies = {"AURSID": maintainer.login(Request(), "testPassword")}
    with client as request:
        request.cookies = cookies
        response = request.get(
            "/packages",
            params={"SB": "w", "SO": "d"},  # Voted  # Descending, Voted first.
        )
    assert response.status_code == int(HTTPStatus.OK)

    root = parse_root(response.text)
    rows = root.xpath('//table[@class="results"]/tbody/tr')
    voted = rows[0].xpath("./td")[5]  # The sixth column of the first row.
    assert voted.text.strip() == "Yes"

    # Conversely, everything else was not voted on.
    voted = rows[1].xpath("./td")[5]  # The sixth column of the second row.
    assert voted.text.strip() == str()  # Empty.


def test_packages_sort_by_notify(
    client: TestClient, maintainer: User, packages: list[Package]
):
    db.create(PackageNotification, PackageBase=packages[0].PackageBase, User=maintainer)

    # Test that, by default, the first result is what we just set above.
    cookies = {"AURSID": maintainer.login(Request(), "testPassword")}
    with client as request:
        request.cookies = cookies
        response = request.get(
            "/packages",
            params={"SB": "o", "SO": "d"},  # Voted  # Descending, Voted first.
        )
    assert response.status_code == int(HTTPStatus.OK)

    root = parse_root(response.text)
    rows = root.xpath('//table[@class="results"]/tbody/tr')
    notify = rows[0].xpath("./td")[6]  # The sixth column of the first row.
    assert notify.text.strip() == "Yes"

    # Conversely, everything else was not voted on.
    notify = rows[1].xpath("./td")[6]  # The sixth column of the second row.
    assert notify.text.strip() == str()  # Empty.


def test_packages_sort_by_maintainer(
    client: TestClient, maintainer: User, package: Package
):
    """Sort a package search by the maintainer column."""

    # Create a second package, so the two can be ordered and checked.
    with db.begin():
        maintainer2 = db.create(
            User,
            Username="maintainer2",
            Email="maintainer2@example.org",
            Passwd="testPassword",
        )
        base2 = db.create(
            PackageBase,
            Name="pkg_2",
            Maintainer=maintainer2,
            Submitter=maintainer2,
            Packager=maintainer2,
        )
        db.create(Package, Name="pkg_2", PackageBase=base2)

    # Check the descending order route.
    with client as request:
        response = request.get("/packages", params={"SB": "m", "SO": "d"})
    assert response.status_code == int(HTTPStatus.OK)

    root = parse_root(response.text)
    rows = root.xpath('//table[@class="results"]/tbody/tr')
    col = rows[0].xpath("./td")[5].xpath("./a")[0]  # Last column.

    assert col.text.strip() == maintainer.Username

    # On the other hand, with ascending, we should get reverse ordering.
    with client as request:
        response = request.get("/packages", params={"SB": "m", "SO": "a"})
    assert response.status_code == int(HTTPStatus.OK)

    root = parse_root(response.text)
    rows = root.xpath('//table[@class="results"]/tbody/tr')
    col = rows[0].xpath("./td")[5].xpath("./a")[0]  # Last column.

    assert col.text.strip() == maintainer2.Username


def test_packages_sort_by_last_modified(client: TestClient, packages: list[Package]):
    now = time.utcnow()
    # Set the first package's ModifiedTS to be 1000 seconds before now.
    package = packages[0]
    with db.begin():
        package.PackageBase.ModifiedTS = now - 1000

    with client as request:
        response = request.get(
            "/packages",
            params={"SB": "l", "SO": "a"},  # Ascending; oldest modification first.
        )
    assert response.status_code == int(HTTPStatus.OK)

    # We should have 50 (default per page) results.
    root = parse_root(response.text)
    rows = root.xpath('//table[@class="results"]/tbody/tr')
    assert len(rows) == 50

    # Let's assert that the first item returned was the one we modified above.
    row = rows[0]
    col = row.xpath("./td")[0].xpath("./a")[0]
    assert col.text.strip() == package.Name

    # Make sure our row contains the modified date we've set
    tz = config.get("options", "default_timezone")
    dt = datetime_display({"timezone": tz}, package.PackageBase.ModifiedTS)
    assert dt in "".join(row.itertext())


def test_packages_flagged(
    client: TestClient, maintainer: User, packages: list[Package]
):
    package = packages[0]

    now = time.utcnow()

    with db.begin():
        package.PackageBase.OutOfDateTS = now
        package.PackageBase.Flagger = maintainer

    with client as request:
        response = request.get("/packages", params={"outdated": "on"})
    assert response.status_code == int(HTTPStatus.OK)

    # We should only get one result from this query; the package we flagged.
    root = parse_root(response.text)
    rows = root.xpath('//table[@class="results"]/tbody/tr')
    assert len(rows) == 1

    with client as request:
        response = request.get("/packages", params={"outdated": "off"})
    assert response.status_code == int(HTTPStatus.OK)

    # In this case, we should get 54 results, which means that the first
    # page will have 50 results (55 packages - 1 outdated = 54 not outdated).
    root = parse_root(response.text)
    rows = root.xpath('//table[@class="results"]/tbody/tr')
    assert len(rows) == 50


def test_packages_orphans(client: TestClient, packages: list[Package]):
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
    """Test the ability for /packages to deal with the PP query
    argument specifications (50, 100, 250; default: 50)."""
    with db.begin():
        for i in range(255):
            base = db.create(
                PackageBase,
                Name=f"pkg_{i}",
                Maintainer=maintainer,
                Submitter=maintainer,
                Packager=maintainer,
            )
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


def test_packages_post_unknown_action(client: TestClient, user: User, package: Package):
    cookies = {"AURSID": user.login(Request(), "testPassword")}
    with client as request:
        request.cookies = cookies
        resp = request.post(
            "/packages",
            data={"action": "unknown"},
        )
    assert resp.status_code == int(HTTPStatus.BAD_REQUEST)


def test_packages_post_error(client: TestClient, user: User, package: Package):
    async def stub_action(request: Request, **kwargs):
        return False, ["Some error."]

    actions = {"stub": stub_action}
    with mock.patch.dict("aurweb.routers.packages.PACKAGE_ACTIONS", actions):
        cookies = {"AURSID": user.login(Request(), "testPassword")}
        with client as request:
            request.cookies = cookies
            resp = request.post(
                "/packages",
                data={"action": "stub"},
            )
        assert resp.status_code == int(HTTPStatus.BAD_REQUEST)

        errors = get_errors(resp.text)
        expected = "Some error."
        assert errors[0].text.strip() == expected


def test_packages_post(client: TestClient, user: User, package: Package):
    async def stub_action(request: Request, **kwargs):
        return True, ["Some success."]

    actions = {"stub": stub_action}
    with mock.patch.dict("aurweb.routers.packages.PACKAGE_ACTIONS", actions):
        cookies = {"AURSID": user.login(Request(), "testPassword")}
        with client as request:
            request.cookies = cookies
            resp = request.post(
                "/packages",
                data={"action": "stub"},
            )
        assert resp.status_code == int(HTTPStatus.OK)

        errors = get_successes(resp.text)
        expected = "Some success."
        assert errors[0].text.strip() == expected


def test_packages_post_unflag(
    client: TestClient, user: User, maintainer: User, package: Package
):
    # Flag `package` as `user`.
    now = time.utcnow()
    with db.begin():
        package.PackageBase.Flagger = user
        package.PackageBase.OutOfDateTS = now

    cookies = {"AURSID": user.login(Request(), "testPassword")}

    # Don't supply any packages.
    post_data = {"action": "unflag", "IDs": []}
    with client as request:
        request.cookies = cookies
        resp = request.post("/packages", data=post_data)
    assert resp.status_code == int(HTTPStatus.BAD_REQUEST)
    errors = get_errors(resp.text)
    expected = "You did not select any packages to unflag."
    assert errors[0].text.strip() == expected

    # Unflag the package as `user`.
    post_data = {"action": "unflag", "IDs": [package.ID]}
    with client as request:
        request.cookies = cookies
        resp = request.post("/packages", data=post_data)
    assert resp.status_code == int(HTTPStatus.OK)
    assert package.PackageBase.Flagger is None
    successes = get_successes(resp.text)
    expected = "The selected packages have been unflagged."
    assert successes[0].text.strip() == expected

    # Re-flag `package` as `user`.
    now = time.utcnow()
    with db.begin():
        package.PackageBase.Flagger = user
        package.PackageBase.OutOfDateTS = now

    # Try to unflag the package as `maintainer`, which is not allowed.
    maint_cookies = {"AURSID": maintainer.login(Request(), "testPassword")}
    post_data = {"action": "unflag", "IDs": [package.ID]}
    with client as request:
        request.cookies = maint_cookies
        resp = request.post("/packages", data=post_data)
    assert resp.status_code == int(HTTPStatus.BAD_REQUEST)
    errors = get_errors(resp.text)
    expected = "You did not select any packages to unflag."
    assert errors[0].text.strip() == expected


def test_packages_post_notify(client: TestClient, user: User, package: Package):
    notif = package.PackageBase.notifications.filter(
        PackageNotification.UserID == user.ID
    ).first()
    assert notif is None

    # Try to enable notifications but supply no packages, causing
    # an error to be rendered.
    cookies = {"AURSID": user.login(Request(), "testPassword")}
    with client as request:
        request.cookies = cookies
        resp = request.post("/packages", data={"action": "notify"})
    assert resp.status_code == int(HTTPStatus.BAD_REQUEST)
    errors = get_errors(resp.text)
    expected = "You did not select any packages to be notified about."
    assert errors[0].text.strip() == expected

    # Now let's actually enable notifications on `package`.
    with client as request:
        request.cookies = cookies
        resp = request.post("/packages", data={"action": "notify", "IDs": [package.ID]})
    assert resp.status_code == int(HTTPStatus.OK)
    expected = "The selected packages' notifications have been enabled."
    successes = get_successes(resp.text)
    assert successes[0].text.strip() == expected

    # Try to enable notifications when they're already enabled,
    # causing an error to be rendered.
    with client as request:
        request.cookies = cookies
        resp = request.post("/packages", data={"action": "notify", "IDs": [package.ID]})
    assert resp.status_code == int(HTTPStatus.BAD_REQUEST)
    errors = get_errors(resp.text)
    expected = "You did not select any packages to be notified about."
    assert errors[0].text.strip() == expected


def test_packages_post_unnotify(client: TestClient, user: User, package: Package):
    # Create a notification record.
    with db.begin():
        notif = db.create(
            PackageNotification, PackageBase=package.PackageBase, User=user
        )
    assert notif is not None

    # Request removal of the notification without any IDs.
    cookies = {"AURSID": user.login(Request(), "testPassword")}
    with client as request:
        request.cookies = cookies
        resp = request.post("/packages", data={"action": "unnotify"})
    assert resp.status_code == int(HTTPStatus.BAD_REQUEST)
    errors = get_errors(resp.text)
    expected = "You did not select any packages for notification removal."
    assert errors[0].text.strip() == expected

    # Request removal of the notification; really.
    with client as request:
        request.cookies = cookies
        resp = request.post(
            "/packages",
            data={"action": "unnotify", "IDs": [package.ID]},
        )
    assert resp.status_code == int(HTTPStatus.OK)
    successes = get_successes(resp.text)
    expected = "The selected packages' notifications have been removed."
    assert successes[0].text.strip() == expected

    # Let's ensure the record got removed.
    notif = package.PackageBase.notifications.filter(
        PackageNotification.UserID == user.ID
    ).first()
    assert notif is None

    # Try it again. The notif no longer exists.
    with client as request:
        request.cookies = cookies
        resp = request.post(
            "/packages",
            data={"action": "unnotify", "IDs": [package.ID]},
        )
    assert resp.status_code == int(HTTPStatus.BAD_REQUEST)
    errors = get_errors(resp.text)
    expected = "A package you selected does not have notifications enabled."
    assert errors[0].text.strip() == expected


def test_packages_post_adopt(client: TestClient, user: User, package: Package):
    # Try to adopt an empty list of packages.
    cookies = {"AURSID": user.login(Request(), "testPassword")}
    with client as request:
        request.cookies = cookies
        resp = request.post("/packages", data={"action": "adopt"})
    assert resp.status_code == int(HTTPStatus.BAD_REQUEST)
    errors = get_errors(resp.text)
    expected = "You did not select any packages to adopt."
    assert errors[0].text.strip() == expected

    # Now, let's try to adopt a package that's already maintained.
    with client as request:
        request.cookies = cookies
        resp = request.post(
            "/packages",
            data={"action": "adopt", "IDs": [package.ID], "confirm": True},
        )
    assert resp.status_code == int(HTTPStatus.BAD_REQUEST)
    errors = get_errors(resp.text)
    expected = "You are not allowed to adopt one of the packages you selected."
    assert errors[0].text.strip() == expected

    # Remove the maintainer from the DB.
    with db.begin():
        package.PackageBase.Maintainer = None
    assert package.PackageBase.Maintainer is None

    # Now, let's try to adopt without confirming.
    with client as request:
        request.cookies = cookies
        resp = request.post("/packages", data={"action": "adopt", "IDs": [package.ID]})
    assert resp.status_code == int(HTTPStatus.BAD_REQUEST)
    errors = get_errors(resp.text)
    expected = (
        "The selected packages have not been adopted, "
        "check the confirmation checkbox."
    )
    assert errors[0].text.strip() == expected

    # Let's do it again now that there is no maintainer.
    with client as request:
        request.cookies = cookies
        resp = request.post(
            "/packages",
            data={"action": "adopt", "IDs": [package.ID], "confirm": True},
        )
    assert resp.status_code == int(HTTPStatus.OK)
    successes = get_successes(resp.text)
    expected = "The selected packages have been adopted."
    assert successes[0].text.strip() == expected


def test_packages_post_disown_as_maintainer(
    client: TestClient, user: User, maintainer: User, package: Package
):
    """Disown packages as a maintainer."""
    # Initially prove that we have a maintainer.
    assert package.PackageBase.Maintainer is not None
    assert package.PackageBase.Maintainer == maintainer

    # Try to run the disown action with no IDs; get an error.
    cookies = {"AURSID": maintainer.login(Request(), "testPassword")}
    with client as request:
        request.cookies = cookies
        resp = request.post("/packages", data={"action": "disown"})
    assert resp.status_code == int(HTTPStatus.BAD_REQUEST)
    errors = get_errors(resp.text)
    expected = "You did not select any packages to disown."
    assert errors[0].text.strip() == expected
    assert package.PackageBase.Maintainer is not None

    # Try to disown `package` without giving the confirm argument.
    with client as request:
        request.cookies = cookies
        resp = request.post("/packages", data={"action": "disown", "IDs": [package.ID]})
    assert resp.status_code == int(HTTPStatus.BAD_REQUEST)
    assert package.PackageBase.Maintainer is not None
    errors = get_errors(resp.text)
    expected = (
        "The selected packages have not been disowned, "
        "check the confirmation checkbox."
    )
    assert errors[0].text.strip() == expected

    # Now, try to disown `package` without credentials (as `user`).
    user_cookies = {"AURSID": user.login(Request(), "testPassword")}
    with client as request:
        request.cookies = user_cookies
        resp = request.post(
            "/packages",
            data={"action": "disown", "IDs": [package.ID], "confirm": True},
        )
    assert resp.status_code == int(HTTPStatus.BAD_REQUEST)
    assert package.PackageBase.Maintainer is not None
    errors = get_errors(resp.text)
    expected = "You are not allowed to disown one of the packages you selected."
    assert errors[0].text.strip() == expected

    # Now, let's really disown `package` as `maintainer`.
    with client as request:
        request.cookies = cookies
        resp = request.post(
            "/packages",
            data={"action": "disown", "IDs": [package.ID], "confirm": True},
        )

    assert package.PackageBase.Maintainer is None
    successes = get_successes(resp.text)
    expected = "The selected packages have been disowned."
    assert successes[0].text.strip() == expected


def test_packages_post_disown(
    client: TestClient, pm_user: User, maintainer: User, package: Package
):
    """Disown packages as a Package Maintainer, which cannot bypass idle time."""
    cookies = {"AURSID": pm_user.login(Request(), "testPassword")}
    with client as request:
        request.cookies = cookies
        resp = request.post(
            "/packages",
            data={"action": "disown", "IDs": [package.ID], "confirm": True},
        )

    errors = get_errors(resp.text)
    expected = r"^No due existing orphan requests to accept for .+\.$"
    assert re.match(expected, errors[0].text.strip())


def test_packages_post_delete(
    caplog: pytest.fixture,
    client: TestClient,
    user: User,
    pm_user: User,
    package: Package,
):
    # First, let's try to use the delete action with no packages IDs.
    user_cookies = {"AURSID": user.login(Request(), "testPassword")}
    with client as request:
        request.cookies = user_cookies
        resp = request.post("/packages", data={"action": "delete"})
    assert resp.status_code == int(HTTPStatus.BAD_REQUEST)
    errors = get_errors(resp.text)
    expected = "You did not select any packages to delete."
    assert errors[0].text.strip() == expected

    # Now, let's try to delete real packages without supplying "confirm".
    with client as request:
        request.cookies = user_cookies
        resp = request.post(
            "/packages",
            data={"action": "delete", "IDs": [package.ID]},
        )
    assert resp.status_code == int(HTTPStatus.BAD_REQUEST)
    errors = get_errors(resp.text)
    expected = (
        "The selected packages have not been deleted, "
        "check the confirmation checkbox."
    )
    assert errors[0].text.strip() == expected

    # And again, with everything, but `user` doesn't have permissions.
    with client as request:
        request.cookies = user_cookies
        resp = request.post(
            "/packages",
            data={"action": "delete", "IDs": [package.ID], "confirm": True},
        )
    assert resp.status_code == int(HTTPStatus.BAD_REQUEST)
    errors = get_errors(resp.text)
    expected = "You do not have permission to delete packages."
    assert errors[0].text.strip() == expected

    # Now, let's switch over to making the requests as a PM.
    # However, this next request will be rejected due to supplying
    # an invalid package ID.
    pm_cookies = {"AURSID": pm_user.login(Request(), "testPassword")}
    with client as request:
        request.cookies = pm_cookies
        resp = request.post(
            "/packages",
            data={"action": "delete", "IDs": [0], "confirm": True},
        )
    assert resp.status_code == int(HTTPStatus.BAD_REQUEST)
    errors = get_errors(resp.text)
    expected = "One of the packages you selected does not exist."
    assert errors[0].text.strip() == expected

    # Whoo. Now, let's finally make a valid request as `pm_user`
    # to delete `package`.
    with client as request:
        request.cookies = pm_cookies
        resp = request.post(
            "/packages",
            data={"action": "delete", "IDs": [package.ID], "confirm": True},
        )
    assert resp.status_code == int(HTTPStatus.OK)
    successes = get_successes(resp.text)
    expected = "The selected packages have been deleted."
    assert successes[0].text.strip() == expected

    # Expect that the package deletion was logged.
    pkgbases = [package.PackageBase.Name]
    expected = (
        f"Privileged user '{pm_user.Username}' deleted the "
        f"following package bases: {str(pkgbases)}."
    )
    assert expected in caplog.text


def test_account_comments_unauthorized(client: TestClient, user: User):
    """This test may seem out of place, but it requires packages,
    so its being included in the packages routes test suite to
    leverage existing fixtures."""
    endpoint = f"/account/{user.Username}/comments"
    with client as request:
        resp = request.get(endpoint)
    assert resp.status_code == int(HTTPStatus.SEE_OTHER)
    assert resp.headers.get("location").startswith("/login")


def test_account_comments(client: TestClient, user: User, package: Package):
    """This test may seem out of place, but it requires packages,
    so its being included in the packages routes test suite to
    leverage existing fixtures."""
    now = time.utcnow()
    with db.begin():
        # This comment's CommentTS is `now + 1`, so it is found in rendered
        # HTML before the rendered_comment, which has a CommentTS of `now`.
        comment = db.create(
            PackageComment,
            PackageBase=package.PackageBase,
            User=user,
            Comments="Test comment",
            CommentTS=now + 1,
        )
        rendered_comment = db.create(
            PackageComment,
            PackageBase=package.PackageBase,
            User=user,
            Comments="Test comment",
            RenderedComment="<p>Test comment</p>",
            CommentTS=now,
        )

    cookies = {"AURSID": user.login(Request(), "testPassword")}
    endpoint = f"/account/{user.Username}/comments"
    with client as request:
        request.cookies = cookies
        resp = request.get(endpoint)
    assert resp.status_code == int(HTTPStatus.OK)

    root = parse_root(resp.text)
    comments = root.xpath('//div[@class="article-content"]/div')

    # Assert that we got Comments rendered from the first comment.
    assert comments[0].text.strip() == comment.Comments

    # And from the second, we have rendered content.
    rendered = comments[1].xpath("./p")
    expected = rendered_comment.RenderedComment.replace("<p>", "").replace("</p>", "")
    assert rendered[0].text.strip() == expected
