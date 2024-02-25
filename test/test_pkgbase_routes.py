import re
from http import HTTPStatus
from unittest import mock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import and_

from aurweb import asgi, config, db, time
from aurweb.models.account_type import USER_ID, AccountType
from aurweb.models.dependency_type import DependencyType
from aurweb.models.package import Package
from aurweb.models.package_base import PackageBase
from aurweb.models.package_comaintainer import PackageComaintainer
from aurweb.models.package_comment import PackageComment
from aurweb.models.package_dependency import PackageDependency
from aurweb.models.package_notification import PackageNotification
from aurweb.models.package_relation import PackageRelation
from aurweb.models.package_request import ACCEPTED_ID, PackageRequest
from aurweb.models.package_vote import PackageVote
from aurweb.models.relation_type import PROVIDES_ID, RelationType
from aurweb.models.request_type import DELETION_ID, MERGE_ID, RequestType
from aurweb.models.user import User
from aurweb.testing.email import Email
from aurweb.testing.html import get_errors, get_successes, parse_root
from aurweb.testing.requests import Request

max_chars_comment = config.getint("options", "max_chars_comment", 5000)


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
def comaintainer() -> User:
    """Yield a specific User used to maintain packages."""
    account_type = db.query(AccountType, AccountType.ID == USER_ID).first()
    with db.begin():
        comaintainer = db.create(
            User,
            Username="test_comaintainer",
            Email="test_comaintainer@example.org",
            Passwd="testPassword",
            AccountType=account_type,
        )
    yield comaintainer


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


@pytest.fixture
def requests(user: User, packages: list[Package]) -> list[PackageRequest]:
    pkgreqs = []
    deletion_type = db.query(RequestType).filter(RequestType.ID == DELETION_ID).first()
    with db.begin():
        for i in range(55):
            pkgreq = db.create(
                PackageRequest,
                RequestType=deletion_type,
                User=user,
                PackageBase=packages[i].PackageBase,
                PackageBaseName=packages[i].Name,
                Comments=f"Deletion request for pkg_{i}",
                ClosureComment=str(),
            )
            pkgreqs.append(pkgreq)
    yield pkgreqs


def test_pkgbase_not_found(client: TestClient):
    with client as request:
        resp = request.get("/pkgbase/not_found")
    assert resp.status_code == int(HTTPStatus.NOT_FOUND)


def test_pkgbase_redirect(client: TestClient, package: Package):
    with client as request:
        resp = request.get(f"/pkgbase/{package.Name}")
    assert resp.status_code == int(HTTPStatus.SEE_OTHER)
    assert resp.headers.get("location") == f"/packages/{package.Name}"


def test_pkgbase(client: TestClient, package: Package):
    with db.begin():
        second = db.create(Package, Name="second-pkg", PackageBase=package.PackageBase)

    expected = [package.Name, second.Name]
    with client as request:
        resp = request.get(f"/pkgbase/{package.Name}")
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


def test_pkgbase_maintainer(
    client: TestClient, user: User, maintainer: User, package: Package
):
    """
    Test that the Maintainer field is beind displayed correctly.

    Co-maintainers are displayed, if they exist, within a parens after
    the maintainer.
    """
    with db.begin():
        db.create(
            PackageComaintainer, User=user, PackageBase=package.PackageBase, Priority=1
        )

    with client as request:
        resp = request.get(f"/pkgbase/{package.Name}", follow_redirects=True)
    assert resp.status_code == int(HTTPStatus.OK)

    root = parse_root(resp.text)

    maint = root.xpath('//table[@id="pkginfo"]/tr[@class="pkgmaint"]/td')[0]
    maint, comaint = maint.text.strip().split()
    assert maint == maintainer.Username
    assert comaint == f"({user.Username})"


def test_pkgbase_voters(client: TestClient, pm_user: User, package: Package):
    pkgbase = package.PackageBase
    endpoint = f"/pkgbase/{pkgbase.Name}/voters"

    now = time.utcnow()
    with db.begin():
        db.create(PackageVote, User=pm_user, PackageBase=pkgbase, VoteTS=now)

    cookies = {"AURSID": pm_user.login(Request(), "testPassword")}
    with client as request:
        request.cookies = cookies
        resp = request.get(endpoint)
    assert resp.status_code == int(HTTPStatus.OK)

    # We should've gotten one link to the voter, pm_user.
    root = parse_root(resp.text)
    rows = root.xpath('//div[@class="box"]//ul/li/a')
    assert len(rows) == 1
    assert rows[0].text.strip() == pm_user.Username


def test_pkgbase_voters_unauthorized(client: TestClient, user: User, package: Package):
    pkgbase = package.PackageBase
    endpoint = f"/pkgbase/{pkgbase.Name}/voters"

    now = time.utcnow()
    with db.begin():
        db.create(PackageVote, User=user, PackageBase=pkgbase, VoteTS=now)

    with client as request:
        resp = request.get(endpoint)
    assert resp.status_code == int(HTTPStatus.SEE_OTHER)
    assert resp.headers.get("location") == f"/pkgbase/{pkgbase.Name}"


def test_pkgbase_comment_not_found(
    client: TestClient, maintainer: User, package: Package
):
    cookies = {"AURSID": maintainer.login(Request(), "testPassword")}
    comment_id = 12345  # A non-existing comment.
    endpoint = f"/pkgbase/{package.PackageBase.Name}/comments/{comment_id}"
    with client as request:
        request.cookies = cookies
        resp = request.post(endpoint, data={"comment": "Failure"})
    assert resp.status_code == int(HTTPStatus.NOT_FOUND)


def test_pkgbase_comment_form_unauthorized(
    client: TestClient, user: User, maintainer: User, package: Package
):
    now = time.utcnow()
    with db.begin():
        comment = db.create(
            PackageComment,
            PackageBase=package.PackageBase,
            User=maintainer,
            Comments="Test",
            RenderedComment=str(),
            CommentTS=now,
        )

    cookies = {"AURSID": user.login(Request(), "testPassword")}
    pkgbasename = package.PackageBase.Name
    endpoint = f"/pkgbase/{pkgbasename}/comments/{comment.ID}/form"
    with client as request:
        request.cookies = cookies
        resp = request.get(endpoint)
    assert resp.status_code == int(HTTPStatus.UNAUTHORIZED)


def test_pkgbase_comment_form_not_found(
    client: TestClient, maintainer: User, package: Package
):
    cookies = {"AURSID": maintainer.login(Request(), "testPassword")}
    comment_id = 12345  # A non-existing comment.
    pkgbasename = package.PackageBase.Name
    endpoint = f"/pkgbase/{pkgbasename}/comments/{comment_id}/form"
    with client as request:
        request.cookies = cookies
        resp = request.get(endpoint)
    assert resp.status_code == int(HTTPStatus.NOT_FOUND)


def test_pkgbase_comments_missing_comment(
    client: TestClient, maintainer: User, package: Package
):
    cookies = {"AURSID": maintainer.login(Request(), "testPassword")}
    endpoint = f"/pkgbase/{package.PackageBase.Name}/comments"
    with client as request:
        request.cookies = cookies
        resp = request.post(endpoint)
    assert resp.status_code == int(HTTPStatus.BAD_REQUEST)


def test_pkgbase_comments(
    client: TestClient, maintainer: User, user: User, package: Package
):
    """This test includes tests against the following routes:
    - GET /pkgbase/{name} (to check notification checkbox)
    - POST /pkgbase/{name}/comments
    - GET /pkgbase/{name} (to check comments)
        - Tested against a comment created with the POST route
    - GET /pkgbase/{name}/comments/{id}/form
        - Tested against a comment created with the POST route
    """
    cookies = {"AURSID": maintainer.login(Request(), "testPassword")}
    pkgbasename = package.PackageBase.Name

    endpoint = f"/pkgbase/{pkgbasename}"
    with client as request:
        request.cookies = cookies
        resp = request.get(
            endpoint,
            follow_redirects=True,
        )
    assert resp.status_code == int(HTTPStatus.OK)

    # Make sure we got our checkbox for enabling notifications
    root = parse_root(resp.text)
    input = root.find('//input[@id="id_enable_notifications"]')
    assert input is not None

    # create notification
    with db.begin():
        user.CommentNotify = 1
        db.create(PackageNotification, PackageBase=package.PackageBase, User=user)

    # post a comment
    endpoint = f"/pkgbase/{pkgbasename}/comments"
    with client as request:
        request.cookies = cookies
        resp = request.post(
            endpoint,
            data={"comment": "Test comment.", "enable_notifications": True},
        )
    assert resp.status_code == int(HTTPStatus.SEE_OTHER)

    # user should've gotten a CommentNotification email.
    assert Email.count() == 1

    expected_prefix = f"/pkgbase/{pkgbasename}"
    prefix_len = len(expected_prefix)
    assert resp.headers.get("location")[:prefix_len] == expected_prefix

    with client as request:
        resp = request.get(resp.headers.get("location"), follow_redirects=True)
    assert resp.status_code == int(HTTPStatus.OK)

    root = parse_root(resp.text)
    headers = root.xpath('//h4[@class="comment-header"]')
    bodies = root.xpath('//div[@class="article-content"]/div/p')

    assert len(headers) == 1
    assert len(bodies) == 1

    assert bodies[0].text.strip() == "Test comment."
    comment_id = headers[0].attrib["id"].split("-")[-1]

    # Since we've enabled notifications already,
    # there should be no checkbox on our page
    input = root.find('//input[@id="id_enable_notifications"]')
    assert input is None

    # Test the non-javascript version of comment editing by
    # visiting the /pkgbase/{name}/comments/{id}/edit route.
    with client as request:
        request.cookies = cookies
        resp = request.get(f"{endpoint}/{comment_id}/edit")
    assert resp.status_code == int(HTTPStatus.OK)

    # Clear up the PackageNotification. This doubles as testing
    # that the notification was created and clears it up so we can
    # test enabling it during edit.
    pkgbase = package.PackageBase
    db_notif = pkgbase.notifications.filter(
        PackageNotification.UserID == maintainer.ID
    ).first()
    with db.begin():
        db.delete(db_notif)

    # Now, let's edit the comment we just created.
    comment_id = int(headers[0].attrib["id"].split("-")[-1])
    endpoint = f"/pkgbase/{pkgbasename}/comments/{comment_id}"
    with client as request:
        request.cookies = cookies
        resp = request.post(
            endpoint,
            data={"comment": "Edited comment.", "enable_notifications": True},
        )
    assert resp.status_code == int(HTTPStatus.SEE_OTHER)

    with client as request:
        resp = request.get(resp.headers.get("location"), follow_redirects=True)
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

    # Now, let's edit again, but cancel.
    endpoint = f"/pkgbase/{pkgbasename}/comments/{comment_id}"
    with client as request:
        request.cookies = cookies
        resp = request.post(
            endpoint,
            data={"comment": "Edited comment with cancel.", "cancel": True},
        )
    assert resp.status_code == int(HTTPStatus.SEE_OTHER)

    with client as request:
        resp = request.get(resp.headers.get("location"), follow_redirects=True)
    assert resp.status_code == int(HTTPStatus.OK)

    root = parse_root(resp.text)
    bodies = root.xpath('//div[@class="article-content"]/div/p')

    # Make sure our comment was NOT changed
    assert bodies[0].text.strip() == "Edited comment."

    # Delete notification for next test.
    with db.begin():
        db.delete(db_notif)

    # Let's edit the comment again; This time we don't change the text.
    # However we do enable notifications.
    with client as request:
        request.cookies = cookies
        resp = request.post(
            endpoint,
            data={"comment": "Edited comment.", "enable_notifications": True},
        )
    assert resp.status_code == int(HTTPStatus.SEE_OTHER)

    # Ensure that a notification was created.
    db_notif = pkgbase.notifications.filter(
        PackageNotification.UserID == maintainer.ID
    ).first()
    assert db_notif is not None

    # Don't supply a comment; should return BAD_REQUEST.
    with client as request:
        request.cookies = cookies
        fail_resp = request.post(endpoint)
    assert fail_resp.status_code == int(HTTPStatus.BAD_REQUEST)

    # Now, test the form route, which should return form markup
    # via JSON.
    endpoint = f"{endpoint}/form"
    with client as request:
        request.cookies = cookies
        resp = request.get(endpoint)
    assert resp.status_code == int(HTTPStatus.OK)

    data = resp.json()
    assert "form" in data


def test_pkgbase_comment_exceed_character_limit(
    client: TestClient,
    user: User,
    package: Package,
    comment: PackageComment,
):
    # Post new comment
    cookies = {"AURSID": user.login(Request(), "testPassword")}
    pkgbasename = package.PackageBase.Name
    endpoint = f"/pkgbase/{pkgbasename}/comments"

    with client as request:
        request.cookies = cookies
        resp = request.post(
            endpoint,
            data={"comment": "x" * (max_chars_comment + 1)},
        )
    assert resp.status_code == int(HTTPStatus.BAD_REQUEST)
    assert "Maximum number of characters for comment exceeded." in resp.text
    # Edit existing
    cookies = {"AURSID": user.login(Request(), "testPassword")}
    with client as request:
        request.cookies = cookies
        endp = f"/pkgbase/{pkgbasename}/comments/{comment.ID}"
        response = request.post(
            endp,
            data={"comment": "x" * (max_chars_comment + 1)},
        )
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert "Maximum number of characters for comment exceeded." in resp.text


def test_pkgbase_comment_edit_unauthorized(
    client: TestClient,
    user: User,
    maintainer: User,
    package: Package,
    comment: PackageComment,
):
    pkgbase = package.PackageBase

    cookies = {"AURSID": maintainer.login(Request(), "testPassword")}
    with client as request:
        request.cookies = cookies
        endp = f"/pkgbase/{pkgbase.Name}/comments/{comment.ID}"
        response = request.post(
            endp,
            data={"comment": "abcd im trying to change this comment."},
        )
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_pkgbase_comment_delete(
    client: TestClient,
    maintainer: User,
    user: User,
    package: Package,
    comment: PackageComment,
):
    # Test the unauthorized case of comment deletion.
    cookies = {"AURSID": user.login(Request(), "testPassword")}
    pkgbasename = package.PackageBase.Name
    endpoint = f"/pkgbase/{pkgbasename}/comments/{comment.ID}/delete"
    with client as request:
        request.cookies = cookies
        resp = request.post(endpoint)
    assert resp.status_code == int(HTTPStatus.SEE_OTHER)

    expected = f"/pkgbase/{pkgbasename}"
    assert resp.headers.get("location") == expected

    # Test the unauthorized case of comment undeletion.
    maint_cookies = {"AURSID": maintainer.login(Request(), "testPassword")}
    endpoint = f"/pkgbase/{pkgbasename}/comments/{comment.ID}/undelete"
    with client as request:
        request.cookies = maint_cookies
        resp = request.post(endpoint)
    assert resp.status_code == int(HTTPStatus.UNAUTHORIZED)

    # And move on to undeleting it.
    with client as request:
        request.cookies = cookies
        resp = request.post(endpoint)
    assert resp.status_code == int(HTTPStatus.SEE_OTHER)


def test_pkgbase_comment_delete_unauthorized(
    client: TestClient, maintainer: User, package: Package, comment: PackageComment
):
    # Test the unauthorized case of comment deletion.
    cookies = {"AURSID": maintainer.login(Request(), "testPassword")}
    pkgbasename = package.PackageBase.Name
    endpoint = f"/pkgbase/{pkgbasename}/comments/{comment.ID}/delete"
    with client as request:
        request.cookies = cookies
        resp = request.post(endpoint)
    assert resp.status_code == int(HTTPStatus.UNAUTHORIZED)


def test_pkgbase_comment_delete_not_found(
    client: TestClient, maintainer: User, package: Package
):
    cookies = {"AURSID": maintainer.login(Request(), "testPassword")}
    comment_id = 12345  # Non-existing comment.
    pkgbasename = package.PackageBase.Name
    endpoint = f"/pkgbase/{pkgbasename}/comments/{comment_id}/delete"
    with client as request:
        request.cookies = cookies
        resp = request.post(endpoint)
    assert resp.status_code == int(HTTPStatus.NOT_FOUND)


def test_pkgbase_comment_undelete_not_found(
    client: TestClient, maintainer: User, package: Package
):
    cookies = {"AURSID": maintainer.login(Request(), "testPassword")}
    comment_id = 12345  # Non-existing comment.
    pkgbasename = package.PackageBase.Name
    endpoint = f"/pkgbase/{pkgbasename}/comments/{comment_id}/undelete"
    with client as request:
        request.cookies = cookies
        resp = request.post(endpoint)
    assert resp.status_code == int(HTTPStatus.NOT_FOUND)


def test_pkgbase_comment_pin_as_co(
    client: TestClient, package: Package, comment: PackageComment
):
    comaint = create_user("comaint1")

    with db.begin():
        db.create(
            PackageComaintainer,
            PackageBase=package.PackageBase,
            User=comaint,
            Priority=1,
        )

    # Pin the comment.
    pkgbasename = package.PackageBase.Name
    endpoint = f"/pkgbase/{pkgbasename}/comments/{comment.ID}/pin"
    cookies = {"AURSID": comaint.login(Request(), "testPassword")}
    with client as request:
        request.cookies = cookies
        resp = request.post(endpoint)
    assert resp.status_code == int(HTTPStatus.SEE_OTHER)

    # Assert that PinnedTS got set.
    assert comment.PinnedTS > 0

    # Unpin the comment we just pinned.
    endpoint = f"/pkgbase/{pkgbasename}/comments/{comment.ID}/unpin"
    with client as request:
        request.cookies = cookies
        resp = request.post(endpoint)
    assert resp.status_code == int(HTTPStatus.SEE_OTHER)

    # Let's assert that PinnedTS was unset.
    assert comment.PinnedTS == 0


def test_pkgbase_comment_pin(
    client: TestClient, maintainer: User, package: Package, comment: PackageComment
):
    cookies = {"AURSID": maintainer.login(Request(), "testPassword")}
    comment_id = comment.ID
    pkgbasename = package.PackageBase.Name

    # Pin the comment.
    endpoint = f"/pkgbase/{pkgbasename}/comments/{comment_id}/pin"
    with client as request:
        request.cookies = cookies
        resp = request.post(endpoint)
    assert resp.status_code == int(HTTPStatus.SEE_OTHER)

    # Assert that PinnedTS got set.
    assert comment.PinnedTS > 0

    # Unpin the comment we just pinned.
    endpoint = f"/pkgbase/{pkgbasename}/comments/{comment_id}/unpin"
    with client as request:
        request.cookies = cookies
        resp = request.post(endpoint)
    assert resp.status_code == int(HTTPStatus.SEE_OTHER)

    # Let's assert that PinnedTS was unset.
    assert comment.PinnedTS == 0


def test_pkgbase_comment_pin_unauthorized(
    client: TestClient, user: User, package: Package, comment: PackageComment
):
    cookies = {"AURSID": user.login(Request(), "testPassword")}
    comment_id = comment.ID
    pkgbasename = package.PackageBase.Name
    endpoint = f"/pkgbase/{pkgbasename}/comments/{comment_id}/pin"
    with client as request:
        request.cookies = cookies
        resp = request.post(endpoint)
    assert resp.status_code == int(HTTPStatus.UNAUTHORIZED)


def test_pkgbase_comment_unpin_unauthorized(
    client: TestClient, user: User, package: Package, comment: PackageComment
):
    cookies = {"AURSID": user.login(Request(), "testPassword")}
    comment_id = comment.ID
    pkgbasename = package.PackageBase.Name
    endpoint = f"/pkgbase/{pkgbasename}/comments/{comment_id}/unpin"
    with client as request:
        request.cookies = cookies
        resp = request.post(endpoint)
    assert resp.status_code == int(HTTPStatus.UNAUTHORIZED)


def test_pkgbase_comaintainers_not_found(client: TestClient, maintainer: User):
    cookies = {"AURSID": maintainer.login(Request(), "testPassword")}
    endpoint = "/pkgbase/fake/comaintainers"
    with client as request:
        request.cookies = cookies
        resp = request.get(endpoint)
    assert resp.status_code == int(HTTPStatus.NOT_FOUND)


def test_pkgbase_comaintainers_post_not_found(client: TestClient, maintainer: User):
    cookies = {"AURSID": maintainer.login(Request(), "testPassword")}
    endpoint = "/pkgbase/fake/comaintainers"
    with client as request:
        request.cookies = cookies
        resp = request.post(endpoint)
    assert resp.status_code == int(HTTPStatus.NOT_FOUND)


def test_pkgbase_comaintainers_unauthorized(
    client: TestClient, user: User, package: Package
):
    pkgbase = package.PackageBase
    endpoint = f"/pkgbase/{pkgbase.Name}/comaintainers"
    cookies = {"AURSID": user.login(Request(), "testPassword")}
    with client as request:
        request.cookies = cookies
        resp = request.get(endpoint)
    assert resp.status_code == int(HTTPStatus.SEE_OTHER)
    assert resp.headers.get("location") == f"/pkgbase/{pkgbase.Name}"


def test_pkgbase_comaintainers_post_unauthorized(
    client: TestClient, user: User, package: Package
):
    pkgbase = package.PackageBase
    endpoint = f"/pkgbase/{pkgbase.Name}/comaintainers"
    cookies = {"AURSID": user.login(Request(), "testPassword")}
    with client as request:
        request.cookies = cookies
        resp = request.post(endpoint)
    assert resp.status_code == int(HTTPStatus.SEE_OTHER)
    assert resp.headers.get("location") == f"/pkgbase/{pkgbase.Name}"


def test_pkgbase_comaintainers_post_invalid_user(
    client: TestClient, maintainer: User, package: Package
):
    pkgbase = package.PackageBase
    endpoint = f"/pkgbase/{pkgbase.Name}/comaintainers"
    cookies = {"AURSID": maintainer.login(Request(), "testPassword")}
    with client as request:
        request.cookies = cookies
        resp = request.post(endpoint, data={"users": "\nfake\n"})
    assert resp.status_code == int(HTTPStatus.OK)

    root = parse_root(resp.text)
    error = root.xpath('//ul[@class="errorlist"]/li')[0]
    assert error.text.strip() == "Invalid user name: fake"


def test_pkgbase_comaintainers(
    client: TestClient, user: User, maintainer: User, package: Package
):
    pkgbase = package.PackageBase
    endpoint = f"/pkgbase/{pkgbase.Name}/comaintainers"
    cookies = {"AURSID": maintainer.login(Request(), "testPassword")}

    # Start off by adding user as a comaintainer to package.
    # The maintainer username given should be ignored.
    with client as request:
        request.cookies = cookies
        resp = request.post(
            endpoint,
            data={"users": f"\n{user.Username}\n{maintainer.Username}\n"},
        )
    assert resp.status_code == int(HTTPStatus.SEE_OTHER)
    assert resp.headers.get("location") == f"/pkgbase/{pkgbase.Name}"

    # Do it again to exercise the last_priority bump path.
    with client as request:
        request.cookies = cookies
        resp = request.post(
            endpoint,
            data={"users": f"\n{user.Username}\n{maintainer.Username}\n"},
        )
    assert resp.status_code == int(HTTPStatus.SEE_OTHER)
    assert resp.headers.get("location") == f"/pkgbase/{pkgbase.Name}"

    # Now that we've added a comaintainer to the pkgbase,
    # let's perform a GET request to make sure that the backend produces
    # the user we added in the users textarea.
    with client as request:
        request.cookies = cookies
        resp = request.get(endpoint)
    assert resp.status_code == int(HTTPStatus.OK)

    root = parse_root(resp.text)
    users = root.xpath('//textarea[@id="id_users"]')[0]
    assert users.text.strip() == user.Username

    # Finish off by removing all the comaintainers.
    with client as request:
        request.cookies = cookies
        resp = request.post(endpoint, data={"users": str()})
    assert resp.status_code == int(HTTPStatus.SEE_OTHER)
    assert resp.headers.get("location") == f"/pkgbase/{pkgbase.Name}"

    with client as request:
        request.cookies = cookies
        resp = request.get(endpoint)
    assert resp.status_code == int(HTTPStatus.OK)

    root = parse_root(resp.text)
    users = root.xpath('//textarea[@id="id_users"]')[0]
    assert users is not None and users.text is None


def test_pkgbase_request_not_found(client: TestClient, user: User):
    pkgbase_name = "fake"
    endpoint = f"/pkgbase/{pkgbase_name}/request"

    cookies = {"AURSID": user.login(Request(), "testPassword")}
    with client as request:
        request.cookies = cookies
        resp = request.get(endpoint)
    assert resp.status_code == int(HTTPStatus.NOT_FOUND)


def test_pkgbase_request(client: TestClient, user: User, package: Package):
    pkgbase = package.PackageBase
    endpoint = f"/pkgbase/{pkgbase.Name}/request"

    cookies = {"AURSID": user.login(Request(), "testPassword")}
    with client as request:
        request.cookies = cookies
        resp = request.get(endpoint)
    assert resp.status_code == int(HTTPStatus.OK)


def test_pkgbase_request_post_not_found(client: TestClient, user: User):
    cookies = {"AURSID": user.login(Request(), "testPassword")}
    with client as request:
        request.cookies = cookies
        resp = request.post("/pkgbase/fake/request", data={"type": "fake"})
    assert resp.status_code == int(HTTPStatus.NOT_FOUND)


def test_pkgbase_request_post_invalid_type(
    client: TestClient, user: User, package: Package
):
    endpoint = f"/pkgbase/{package.PackageBase.Name}/request"
    cookies = {"AURSID": user.login(Request(), "testPassword")}
    with client as request:
        request.cookies = cookies
        resp = request.post(endpoint, data={"type": "fake"})
    assert resp.status_code == int(HTTPStatus.BAD_REQUEST)


def test_pkgbase_request_post_no_comment_error(
    client: TestClient, user: User, package: Package
):
    endpoint = f"/pkgbase/{package.PackageBase.Name}/request"
    cookies = {"AURSID": user.login(Request(), "testPassword")}
    with client as request:
        request.cookies = cookies
        resp = request.post(
            endpoint,
            data={
                "type": "deletion",
                "comments": "",  # An empty comment field causes an error.
            },
        )
    assert resp.status_code == int(HTTPStatus.OK)

    root = parse_root(resp.text)
    error = root.xpath('//ul[@class="errorlist"]/li')[0]
    expected = "The comment field must not be empty."
    assert error.text.strip() == expected


def test_pkgbase_request_post_comment_exceed_character_limit(
    client: TestClient, user: User, package: Package
):
    endpoint = f"/pkgbase/{package.PackageBase.Name}/request"
    cookies = {"AURSID": user.login(Request(), "testPassword")}
    with client as request:
        request.cookies = cookies
        resp = request.post(
            endpoint,
            data={
                "type": "deletion",
                "comments": "x" * (max_chars_comment + 1),
            },
        )
    assert resp.status_code == int(HTTPStatus.OK)

    root = parse_root(resp.text)
    error = root.xpath('//ul[@class="errorlist"]/li')[0]
    expected = "Maximum number of characters for comment exceeded."
    assert error.text.strip() == expected


def test_pkgbase_request_post_merge_not_found_error(
    client: TestClient, user: User, package: Package
):
    endpoint = f"/pkgbase/{package.PackageBase.Name}/request"
    cookies = {"AURSID": user.login(Request(), "testPassword")}
    with client as request:
        request.cookies = cookies
        resp = request.post(
            endpoint,
            data={
                "type": "merge",
                "merge_into": "fake",  # There is no PackageBase.Name "fake"
                "comments": "We want to merge this.",
            },
        )
    assert resp.status_code == int(HTTPStatus.OK)

    root = parse_root(resp.text)
    error = root.xpath('//ul[@class="errorlist"]/li')[0]
    expected = "The package base you want to merge into does not exist."
    assert error.text.strip() == expected


def test_pkgbase_request_post_merge_no_merge_into_error(
    client: TestClient, user: User, package: Package
):
    endpoint = f"/pkgbase/{package.PackageBase.Name}/request"
    cookies = {"AURSID": user.login(Request(), "testPassword")}
    with client as request:
        request.cookies = cookies
        resp = request.post(
            endpoint,
            data={
                "type": "merge",
                "merge_into": "",  # There is no PackageBase.Name "fake"
                "comments": "We want to merge this.",
            },
        )
    assert resp.status_code == int(HTTPStatus.OK)

    root = parse_root(resp.text)
    error = root.xpath('//ul[@class="errorlist"]/li')[0]
    expected = 'The "Merge into" field must not be empty.'
    assert error.text.strip() == expected


def test_pkgbase_request_post_merge_self_error(
    client: TestClient, user: User, package: Package
):
    endpoint = f"/pkgbase/{package.PackageBase.Name}/request"
    cookies = {"AURSID": user.login(Request(), "testPassword")}
    with client as request:
        request.cookies = cookies
        resp = request.post(
            endpoint,
            data={
                "type": "merge",
                "merge_into": package.PackageBase.Name,
                "comments": "We want to merge this.",
            },
        )
    assert resp.status_code == int(HTTPStatus.OK)

    root = parse_root(resp.text)
    error = root.xpath('//ul[@class="errorlist"]/li')[0]
    expected = "You cannot merge a package base into itself."
    assert error.text.strip() == expected


def test_pkgbase_flag(
    client: TestClient, user: User, maintainer: User, package: Package
):
    pkgbase = package.PackageBase

    # We shouldn't have flagged the package yet; assert so.
    assert pkgbase.OutOfDateTS is None

    cookies = {"AURSID": user.login(Request(), "testPassword")}
    endpoint = f"/pkgbase/{pkgbase.Name}/flag"

    # Get the flag page.
    with client as request:
        request.cookies = cookies
        resp = request.get(endpoint)
    assert resp.status_code == int(HTTPStatus.OK)

    # Now, let's check the /pkgbase/{name}/flag-comment route.
    flag_comment_endpoint = f"/pkgbase/{pkgbase.Name}/flag-comment"
    with client as request:
        request.cookies = cookies
        resp = request.get(flag_comment_endpoint)
    assert resp.status_code == int(HTTPStatus.SEE_OTHER)
    assert resp.headers.get("location") == f"/pkgbase/{pkgbase.Name}"

    # Try to flag it without a comment.
    with client as request:
        request.cookies = cookies
        resp = request.post(endpoint)
    assert resp.status_code == int(HTTPStatus.BAD_REQUEST)

    # Flag it with a valid comment.
    with client as request:
        request.cookies = cookies
        resp = request.post(endpoint, data={"comments": "Test"})
    assert resp.status_code == int(HTTPStatus.SEE_OTHER)
    assert pkgbase.Flagger == user
    assert pkgbase.FlaggerComment == "Test"

    # Should've gotten a FlagNotification.
    assert Email.count() == 1

    # Now, let's check the /pkgbase/{name}/flag-comment route.
    flag_comment_endpoint = f"/pkgbase/{pkgbase.Name}/flag-comment"
    with client as request:
        request.cookies = cookies
        resp = request.get(flag_comment_endpoint)
    assert resp.status_code == int(HTTPStatus.OK)

    # Now try to perform a get; we should be redirected because
    # it's already flagged.
    with client as request:
        request.cookies = cookies
        resp = request.get(endpoint)
    assert resp.status_code == int(HTTPStatus.SEE_OTHER)

    with db.begin():
        user2 = db.create(
            User,
            Username="test2",
            Email="test2@example.org",
            Passwd="testPassword",
            AccountType=user.AccountType,
        )

    # Now, test that the 'user2' user can't unflag it, because they
    # didn't flag it to begin with.
    user2_cookies = {"AURSID": user2.login(Request(), "testPassword")}
    endpoint = f"/pkgbase/{pkgbase.Name}/unflag"
    with client as request:
        request.cookies = user2_cookies
        resp = request.post(endpoint)
    assert resp.status_code == int(HTTPStatus.SEE_OTHER)
    assert pkgbase.Flagger == user

    # Now, test that the 'maintainer' user can.
    maint_cookies = {"AURSID": maintainer.login(Request(), "testPassword")}
    with client as request:
        request.cookies = maint_cookies
        resp = request.post(endpoint)
    assert resp.status_code == int(HTTPStatus.SEE_OTHER)
    assert pkgbase.Flagger is None

    # Try flagging with a comment that exceeds our character limit.
    with client as request:
        request.cookies = cookies
        data = {"comments": "x" * (max_chars_comment + 1)}
        resp = request.post(f"/pkgbase/{pkgbase.Name}/flag", data=data)
    assert resp.status_code == int(HTTPStatus.BAD_REQUEST)

    # Flag it again.
    with client as request:
        request.cookies = cookies
        resp = request.post(f"/pkgbase/{pkgbase.Name}/flag", data={"comments": "Test"})
    assert resp.status_code == int(HTTPStatus.SEE_OTHER)

    # Now, unflag it for real.
    with client as request:
        request.cookies = cookies
        resp = request.post(endpoint)
    assert resp.status_code == int(HTTPStatus.SEE_OTHER)
    assert pkgbase.Flagger is None


def test_pkgbase_flag_vcs(client: TestClient, user: User, package: Package):
    # Morph our package fixture into a VCS package (-git).
    with db.begin():
        package.PackageBase.Name += "-git"
        package.Name += "-git"

    cookies = {"AURSID": user.login(Request(), "testPassword")}
    with client as request:
        request.cookies = cookies
        resp = request.get(f"/pkgbase/{package.PackageBase.Name}/flag")
    assert resp.status_code == int(HTTPStatus.OK)

    expected = (
        "This seems to be a VCS package. Please do "
        "<strong>not</strong> flag it out-of-date if the package "
        "version in the AUR does not match the most recent commit. "
        "Flagging this package should only be done if the sources "
        "moved or changes in the PKGBUILD are required because of "
        "recent upstream changes."
    )
    assert expected in resp.text


def test_pkgbase_notify(client: TestClient, user: User, package: Package):
    pkgbase = package.PackageBase

    # We have no notif record yet; assert that.
    notif = pkgbase.notifications.filter(PackageNotification.UserID == user.ID).first()
    assert notif is None

    # Enable notifications.
    cookies = {"AURSID": user.login(Request(), "testPassword")}
    endpoint = f"/pkgbase/{pkgbase.Name}/notify"
    with client as request:
        request.cookies = cookies
        resp = request.post(endpoint)
    assert resp.status_code == int(HTTPStatus.SEE_OTHER)

    notif = pkgbase.notifications.filter(PackageNotification.UserID == user.ID).first()
    assert notif is not None

    # Disable notifications.
    endpoint = f"/pkgbase/{pkgbase.Name}/unnotify"
    with client as request:
        request.cookies = cookies
        resp = request.post(endpoint)
    assert resp.status_code == int(HTTPStatus.SEE_OTHER)

    notif = pkgbase.notifications.filter(PackageNotification.UserID == user.ID).first()
    assert notif is None


def test_pkgbase_vote(client: TestClient, user: User, package: Package):
    pkgbase = package.PackageBase

    # We haven't voted yet.
    vote = pkgbase.package_votes.filter(PackageVote.UsersID == user.ID).first()
    assert vote is None

    # Vote for the package.
    cookies = {"AURSID": user.login(Request(), "testPassword")}
    endpoint = f"/pkgbase/{pkgbase.Name}/vote"
    with client as request:
        request.cookies = cookies
        resp = request.post(endpoint)
    assert resp.status_code == int(HTTPStatus.SEE_OTHER)

    vote = pkgbase.package_votes.filter(PackageVote.UsersID == user.ID).first()
    assert vote is not None
    assert pkgbase.NumVotes == 1

    # Remove vote.
    endpoint = f"/pkgbase/{pkgbase.Name}/unvote"
    with client as request:
        request.cookies = cookies
        resp = request.post(endpoint)
    assert resp.status_code == int(HTTPStatus.SEE_OTHER)

    vote = pkgbase.package_votes.filter(PackageVote.UsersID == user.ID).first()
    assert vote is None
    assert pkgbase.NumVotes == 0


def test_pkgbase_disown_as_sole_maintainer(
    client: TestClient, maintainer: User, package: Package
):
    cookies = {"AURSID": maintainer.login(Request(), "testPassword")}
    pkgbase = package.PackageBase
    endpoint = f"/pkgbase/{pkgbase.Name}/disown"

    # But we do here.
    with client as request:
        request.cookies = cookies
        resp = request.post(endpoint, data={"confirm": True})
    assert resp.status_code == int(HTTPStatus.SEE_OTHER)


def test_pkgbase_disown_as_maint_with_comaint(
    client: TestClient, user: User, maintainer: User, package: Package
):
    """When disowning as a maintainer, the lowest priority comaintainer
    is promoted to maintainer."""
    pkgbase = package.PackageBase
    endp = f"/pkgbase/{pkgbase.Name}/disown"
    post_data = {"confirm": True}

    with db.begin():
        db.create(PackageComaintainer, PackageBase=pkgbase, User=user, Priority=1)

    maint_cookies = {"AURSID": maintainer.login(Request(), "testPassword")}
    with client as request:
        request.cookies = maint_cookies
        resp = request.post(endp, data=post_data, follow_redirects=True)
    assert resp.status_code == int(HTTPStatus.OK)

    package = db.refresh(package)
    pkgbase = package.PackageBase

    assert pkgbase.Maintainer == user
    assert pkgbase.comaintainers.count() == 0


def test_pkgbase_disown(
    client: TestClient,
    user: User,
    maintainer: User,
    comaintainer: User,
    package: Package,
):
    maint_cookies = {"AURSID": maintainer.login(Request(), "testPassword")}
    comaint_cookies = {"AURSID": comaintainer.login(Request(), "testPassword")}
    user_cookies = {"AURSID": user.login(Request(), "testPassword")}
    pkgbase = package.PackageBase
    pkgbase_endp = f"/pkgbase/{pkgbase.Name}"
    endpoint = f"{pkgbase_endp}/disown"

    with db.begin():
        db.create(
            PackageComaintainer, User=comaintainer, PackageBase=pkgbase, Priority=1
        )

    # GET as a normal user, which is rejected for lack of credentials.
    with client as request:
        request.cookies = user_cookies
        resp = request.get(endpoint)
    assert resp.status_code == int(HTTPStatus.SEE_OTHER)

    # GET as a comaintainer.
    with client as request:
        request.cookies = comaint_cookies
        resp = request.get(endpoint)
    assert resp.status_code == int(HTTPStatus.OK)

    # Ensure that the comaintainer can see "Disown Package" link
    with client as request:
        request.cookies = comaint_cookies
        resp = request.get(pkgbase_endp, follow_redirects=True)
    assert "Disown Package" in resp.text

    # GET as the maintainer.
    with client as request:
        request.cookies = maint_cookies
        resp = request.get(endpoint)
    assert resp.status_code == int(HTTPStatus.OK)

    # Ensure that the maintainer can see "Disown Package" link
    with client as request:
        request.cookies = maint_cookies
        resp = request.get(pkgbase_endp, follow_redirects=True)
    assert "Disown Package" in resp.text

    # POST as a normal user, which is rejected for lack of credentials.
    with client as request:
        request.cookies = user_cookies
        resp = request.post(endpoint)
    assert resp.status_code == int(HTTPStatus.SEE_OTHER)

    # POST as the comaintainer without "confirm".
    with client as request:
        request.cookies = comaint_cookies
        resp = request.post(endpoint)
    assert resp.status_code == int(HTTPStatus.BAD_REQUEST)

    # POST as the maintainer without "confirm".
    with client as request:
        request.cookies = maint_cookies
        resp = request.post(endpoint)
    assert resp.status_code == int(HTTPStatus.BAD_REQUEST)

    # POST as the comaintainer with "confirm".
    with client as request:
        request.cookies = comaint_cookies
        resp = request.post(endpoint, data={"confirm": True})
    assert resp.status_code == int(HTTPStatus.SEE_OTHER)

    # POST as the maintainer with "confirm".
    with client as request:
        request.cookies = maint_cookies
        resp = request.post(endpoint, data={"confirm": True})
    assert resp.status_code == int(HTTPStatus.SEE_OTHER)


def test_pkgbase_adopt(
    client: TestClient, user: User, pm_user: User, maintainer: User, package: Package
):
    # Unset the maintainer as if package is orphaned.
    with db.begin():
        package.PackageBase.Maintainer = None

    pkgbasename = package.PackageBase.Name
    cookies = {"AURSID": maintainer.login(Request(), "testPassword")}
    endpoint = f"/pkgbase/{pkgbasename}/adopt"

    # Adopt the package base.
    with client as request:
        request.cookies = cookies
        resp = request.post(endpoint)
    assert resp.status_code == int(HTTPStatus.SEE_OTHER)
    assert package.PackageBase.Maintainer == maintainer

    # Try to adopt it when it already has a maintainer; nothing changes.
    user_cookies = {"AURSID": user.login(Request(), "testPassword")}
    with client as request:
        request.cookies = user_cookies
        resp = request.post(endpoint)
    assert resp.status_code == int(HTTPStatus.SEE_OTHER)
    assert package.PackageBase.Maintainer == maintainer

    # Steal the package as a PM.
    pm_cookies = {"AURSID": pm_user.login(Request(), "testPassword")}
    with client as request:
        request.cookies = pm_cookies
        resp = request.post(endpoint)
    assert resp.status_code == int(HTTPStatus.SEE_OTHER)
    assert package.PackageBase.Maintainer == pm_user


def test_pkgbase_delete_unauthorized(client: TestClient, user: User, package: Package):
    pkgbase = package.PackageBase
    cookies = {"AURSID": user.login(Request(), "testPassword")}
    endpoint = f"/pkgbase/{pkgbase.Name}/delete"

    # Test GET.
    with client as request:
        request.cookies = cookies
        resp = request.get(endpoint)
    assert resp.status_code == int(HTTPStatus.SEE_OTHER)
    assert resp.headers.get("location") == f"/pkgbase/{pkgbase.Name}"

    # Test POST.
    with client as request:
        request.cookies = cookies
        resp = request.post(endpoint)
    assert resp.status_code == int(HTTPStatus.SEE_OTHER)
    assert resp.headers.get("location") == f"/pkgbase/{pkgbase.Name}"


def test_pkgbase_delete(client: TestClient, pm_user: User, package: Package):
    pkgbase = package.PackageBase

    # Test that the GET request works.
    cookies = {"AURSID": pm_user.login(Request(), "testPassword")}
    endpoint = f"/pkgbase/{pkgbase.Name}/delete"
    with client as request:
        request.cookies = cookies
        resp = request.get(endpoint)
    assert resp.status_code == int(HTTPStatus.OK)

    # Test that POST works and denies us because we haven't confirmed.
    with client as request:
        request.cookies = cookies
        resp = request.post(endpoint)
    assert resp.status_code == int(HTTPStatus.BAD_REQUEST)

    # Test that we can actually delete the pkgbase.
    with client as request:
        request.cookies = cookies
        resp = request.post(endpoint, data={"confirm": True})
    assert resp.status_code == int(HTTPStatus.SEE_OTHER)

    # Let's assert that the package base record got removed.
    record = db.query(PackageBase).filter(PackageBase.Name == pkgbase.Name).first()
    assert record is None

    # Two emails should've been sent out; an autogenerated
    # request's accepted notification and a deletion notification.
    assert Email.count() == 1

    req_close = Email(1).parse()
    expr = r"^\[PRQ#\d+\] Deletion Request for [^ ]+ Accepted$"
    subject = req_close.headers.get("Subject")
    assert re.match(expr, subject)


def test_pkgbase_delete_with_request(
    client: TestClient, pm_user: User, pkgbase: PackageBase, pkgreq: PackageRequest
):
    # TODO: Test that a previously existing request gets Accepted when
    # a PM deleted the package.

    # Delete the package as `pm_user` via POST request.
    cookies = {"AURSID": pm_user.login(Request(), "testPassword")}
    endpoint = f"/pkgbase/{pkgbase.Name}/delete"
    with client as request:
        request.cookies = cookies
        resp = request.post(endpoint, data={"confirm": True})
    assert resp.status_code == int(HTTPStatus.SEE_OTHER)
    assert resp.headers.get("location") == "/packages"

    # We should've just sent one closure email since `pkgreq` exists.
    assert Email.count() == 1

    # Make sure it was a closure for the deletion request.
    email = Email(1).parse()
    expr = r"^\[PRQ#\d+\] Deletion Request for [^ ]+ Accepted$"
    assert re.match(expr, email.headers.get("Subject"))


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


def test_pkgbase_merge_unauthorized(client: TestClient, user: User, package: Package):
    cookies = {"AURSID": user.login(Request(), "testPassword")}
    endpoint = f"/pkgbase/{package.PackageBase.Name}/merge"
    with client as request:
        request.cookies = cookies
        resp = request.get(endpoint)
    assert resp.status_code == int(HTTPStatus.UNAUTHORIZED)


def test_pkgbase_merge(client: TestClient, pm_user: User, package: Package):
    cookies = {"AURSID": pm_user.login(Request(), "testPassword")}
    endpoint = f"/pkgbase/{package.PackageBase.Name}/merge"
    with client as request:
        request.cookies = cookies
        resp = request.get(endpoint)
    assert resp.status_code == int(HTTPStatus.OK)
    assert not get_errors(resp.text)


def test_pkgbase_merge_post_unauthorized(
    client: TestClient, user: User, package: Package
):
    cookies = {"AURSID": user.login(Request(), "testPassword")}
    endpoint = f"/pkgbase/{package.PackageBase.Name}/merge"
    with client as request:
        request.cookies = cookies
        resp = request.post(endpoint)
    assert resp.status_code == int(HTTPStatus.UNAUTHORIZED)


def test_pkgbase_merge_post_unconfirmed(
    client: TestClient, pm_user: User, package: Package
):
    cookies = {"AURSID": pm_user.login(Request(), "testPassword")}
    endpoint = f"/pkgbase/{package.PackageBase.Name}/merge"
    with client as request:
        request.cookies = cookies
        resp = request.post(endpoint)
    assert resp.status_code == int(HTTPStatus.BAD_REQUEST)
    errors = get_errors(resp.text)
    expected = (
        "The selected packages have not been deleted, "
        "check the confirmation checkbox."
    )
    assert errors[0].text.strip() == expected


def test_pkgbase_merge_post_invalid_into(
    client: TestClient, pm_user: User, package: Package
):
    cookies = {"AURSID": pm_user.login(Request(), "testPassword")}
    endpoint = f"/pkgbase/{package.PackageBase.Name}/merge"
    with client as request:
        request.cookies = cookies
        resp = request.post(endpoint, data={"into": "not_real", "confirm": True})
    assert resp.status_code == int(HTTPStatus.BAD_REQUEST)
    errors = get_errors(resp.text)
    expected = "Cannot find package to merge votes and comments into."
    assert errors[0].text.strip() == expected


def test_pkgbase_merge_post_self_invalid(
    client: TestClient, pm_user: User, package: Package
):
    cookies = {"AURSID": pm_user.login(Request(), "testPassword")}
    endpoint = f"/pkgbase/{package.PackageBase.Name}/merge"
    with client as request:
        request.cookies = cookies
        resp = request.post(
            endpoint,
            data={"into": package.PackageBase.Name, "confirm": True},
        )
    assert resp.status_code == int(HTTPStatus.BAD_REQUEST)
    errors = get_errors(resp.text)
    expected = "Cannot merge a package base with itself."
    assert errors[0].text.strip() == expected


def test_pkgbase_merge_post(
    client: TestClient,
    pm_user: User,
    package: Package,
    pkgbase: PackageBase,
    target: PackageBase,
    pkgreq: PackageRequest,
):
    pkgname = package.Name
    pkgbasename = pkgbase.Name

    # Create a merge request destined for another target.
    # This will allow our test code to exercise closing
    # such a request after merging the pkgbase in question.
    with db.begin():
        pkgreq.ReqTypeID = MERGE_ID
        pkgreq.MergeBaseName = target.Name

    # Vote for the package.
    cookies = {"AURSID": pm_user.login(Request(), "testPassword")}
    endpoint = f"/pkgbase/{package.PackageBase.Name}/vote"
    with client as request:
        request.cookies = cookies
        resp = request.post(endpoint)
    assert resp.status_code == int(HTTPStatus.SEE_OTHER)

    # Enable notifications.
    endpoint = f"/pkgbase/{package.PackageBase.Name}/notify"
    with client as request:
        request.cookies = cookies
        resp = request.post(endpoint)
    assert resp.status_code == int(HTTPStatus.SEE_OTHER)

    # Comment on the package.
    endpoint = f"/pkgbase/{package.PackageBase.Name}/comments"
    with client as request:
        request.cookies = cookies
        resp = request.post(
            endpoint,
            data={"comment": "Test comment."},
        )
    assert resp.status_code == int(HTTPStatus.SEE_OTHER)

    # Save these relationships for later comparison.
    comments = package.PackageBase.comments.all()
    notifs = package.PackageBase.notifications.all()
    votes = package.PackageBase.package_votes.all()

    # Merge the package into target.
    endpoint = f"/pkgbase/{package.PackageBase.Name}/merge"
    with client as request:
        request.cookies = cookies
        resp = request.post(endpoint, data={"into": target.Name, "confirm": True})
    assert resp.status_code == int(HTTPStatus.SEE_OTHER)
    loc = resp.headers.get("location")
    assert loc == f"/pkgbase/{target.Name}"

    # Two emails should've been sent out.
    assert Email.count() == 1
    email_body = Email(1).parse().glue()
    assert f"Merge Request for {pkgbasename} Accepted" in email_body

    # Assert that the original comments, notifs and votes we setup
    # got migrated to target as intended.
    assert comments == target.comments.all()
    assert notifs == target.notifications.all()
    assert votes == target.package_votes.all()

    # ...and that the package got deleted.
    package = db.query(Package).filter(Package.Name == pkgname).first()
    assert package is None

    # Our previously-made request should have gotten accepted.
    assert pkgreq.Status == ACCEPTED_ID
    assert pkgreq.Closer is not None

    # A PackageRequest is always created when merging this way.
    pkgreq = (
        db.query(PackageRequest)
        .filter(
            and_(
                PackageRequest.ReqTypeID == MERGE_ID,
                PackageRequest.PackageBaseName == pkgbasename,
                PackageRequest.MergeBaseName == target.Name,
            )
        )
        .first()
    )
    assert pkgreq is not None


def test_pkgbase_keywords(client: TestClient, user: User, package: Package):
    endpoint = f"/pkgbase/{package.PackageBase.Name}"
    with client as request:
        resp = request.get(endpoint, follow_redirects=True)
    assert resp.status_code == int(HTTPStatus.OK)

    root = parse_root(resp.text)
    keywords = root.xpath('//a[@class="keyword"]')
    assert len(keywords) == 0

    maint = package.PackageBase.Maintainer
    cookies = {"AURSID": maint.login(Request(), "testPassword")}
    post_endpoint = f"{endpoint}/keywords"
    with client as request:
        request.cookies = cookies
        resp = request.post(
            post_endpoint,
            data={"keywords": "abc test"},
        )
    assert resp.status_code == int(HTTPStatus.SEE_OTHER)

    with client as request:
        request.cookies = {}
        resp = request.get(resp.headers.get("location"), follow_redirects=True)
    assert resp.status_code == int(HTTPStatus.OK)

    root = parse_root(resp.text)
    keywords = root.xpath('//a[@class="keyword"]')
    assert len(keywords) == 2
    expected = ["abc", "test"]
    for i, keyword in enumerate(keywords):
        assert keyword.text.strip() == expected[i]


def test_pkgbase_empty_keywords(client: TestClient, user: User, package: Package):
    endpoint = f"/pkgbase/{package.PackageBase.Name}"
    with client as request:
        request.cookies = {}
        resp = request.get(endpoint, follow_redirects=True)
    assert resp.status_code == int(HTTPStatus.OK)

    root = parse_root(resp.text)
    keywords = root.xpath('//a[@class="keyword"]')
    assert len(keywords) == 0

    maint = package.PackageBase.Maintainer
    cookies = {"AURSID": maint.login(Request(), "testPassword")}
    post_endpoint = f"{endpoint}/keywords"
    with client as request:
        request.cookies = cookies
        resp = request.post(
            post_endpoint,
            data={"keywords": "abc test     foo bar    "},
        )
    assert resp.status_code == int(HTTPStatus.SEE_OTHER)

    with client as request:
        request.cookies = {}
        resp = request.get(resp.headers.get("location"), follow_redirects=True)
    assert resp.status_code == int(HTTPStatus.OK)

    root = parse_root(resp.text)
    keywords = root.xpath('//a[@class="keyword"]')
    assert len(keywords) == 4
    expected = ["abc", "bar", "foo", "test"]
    for i, keyword in enumerate(keywords):
        assert keyword.text.strip() == expected[i]


def test_unauthorized_pkgbase_keywords(client: TestClient, package: Package):
    with db.begin():
        user = db.create(
            User, Username="random_user", Email="random_user", Passwd="testPassword"
        )

    cookies = {"AURSID": user.login(Request(), "testPassword")}
    with client as request:
        request.cookies = cookies
        pkgbase = package.PackageBase
        endp = f"/pkgbase/{pkgbase.Name}/keywords"
        response = request.post(endp)
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_independent_user_unflag(client: TestClient, user: User, package: Package):
    with db.begin():
        flagger = db.create(
            User,
            Username="test_flagger",
            Email="test_flagger@example.com",
            Passwd="testPassword",
        )

    pkgbase = package.PackageBase
    cookies = {"AURSID": flagger.login(Request(), "testPassword")}
    with client as request:
        request.cookies = cookies
        endp = f"/pkgbase/{pkgbase.Name}/flag"
        response = request.post(
            endp,
            data={"comments": "This thing needs a flag!"},
            follow_redirects=True,
        )
    assert response.status_code == HTTPStatus.OK

    # At this point, we've flagged it as `flagger`.
    # Now, we should be able to view the "Unflag package" link on the package
    # page when browsing as that `flagger` user.
    with client as request:
        endp = f"/pkgbase/{pkgbase.Name}"
        request.cookies = cookies
        response = request.get(endp, follow_redirects=True)
    assert response.status_code == HTTPStatus.OK

    # Assert that the "Unflag package" link appears in the DOM.
    root = parse_root(response.text)
    elems = root.xpath('//input[@name="do_UnFlag"]')
    assert len(elems) == 1

    # Now, unflag the package by "clicking" the "Unflag package" link.
    with client as request:
        endp = f"/pkgbase/{pkgbase.Name}/unflag"
        request.cookies = cookies
        response = request.post(endp, follow_redirects=True)
    assert response.status_code == HTTPStatus.OK

    # For the last time, let's check the GET response. The package should
    # not show as flagged anymore, and thus the "Unflag package" link
    # should be missing.
    with client as request:
        endp = f"/pkgbase/{pkgbase.Name}"
        request.cookies = cookies
        response = request.get(endp, follow_redirects=True)
    assert response.status_code == HTTPStatus.OK

    # Assert that the "Unflag package" link does not appear in the DOM.
    root = parse_root(response.text)
    elems = root.xpath('//input[@name="do_UnFlag"]')
    assert len(elems) == 0
