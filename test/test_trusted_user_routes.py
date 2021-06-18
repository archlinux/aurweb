import re

from datetime import datetime
from http import HTTPStatus
from io import StringIO

import lxml.etree
import pytest

from fastapi.testclient import TestClient

from aurweb import db
from aurweb.models.account_type import AccountType
from aurweb.models.tu_vote import TUVote
from aurweb.models.tu_voteinfo import TUVoteInfo
from aurweb.models.user import User
from aurweb.testing import setup_test_db
from aurweb.testing.requests import Request

DATETIME_REGEX = r'^[0-9]{4}-[0-9]{2}-[0-9]{2}$'


def parse_root(html):
    parser = lxml.etree.HTMLParser(recover=True)
    tree = lxml.etree.parse(StringIO(html), parser)
    return tree.getroot()


def get_table(root, class_name):
    table = root.xpath(f'//table[contains(@class, "{class_name}")]')[0]
    return table


def get_table_rows(table):
    tbody = table.xpath("./tbody")[0]
    return tbody.xpath("./tr")


def get_pkglist_directions(table):
    stats = table.getparent().xpath("./div[@class='pkglist-stats']")[0]
    nav = stats.xpath("./p[@class='pkglist-nav']")[0]
    return nav.xpath("./a")


def get_a(node):
    return node.xpath('./a')[0].text.strip()


def get_span(node):
    return node.xpath('./span')[0].text.strip()


def assert_current_vote_html(row, expected):
    columns = row.xpath("./td")
    proposal, start, end, user, voted = columns
    p, s, e, u, v = expected  # Column expectations.
    assert re.match(p, get_a(proposal)) is not None
    assert re.match(s, start.text) is not None
    assert re.match(e, end.text) is not None
    assert re.match(u, get_a(user)) is not None
    assert re.match(v, get_span(voted)) is not None


def assert_past_vote_html(row, expected):
    columns = row.xpath("./td")
    proposal, start, end, user, yes, no, voted = columns  # Real columns.
    p, s, e, u, y, n, v = expected  # Column expectations.
    assert re.match(p, get_a(proposal)) is not None
    assert re.match(s, start.text) is not None
    assert re.match(e, end.text) is not None
    assert re.match(u, get_a(user)) is not None
    assert re.match(y, yes.text) is not None
    assert re.match(n, no.text) is not None
    assert re.match(v, get_span(voted)) is not None


@pytest.fixture(autouse=True)
def setup():
    setup_test_db("TU_Votes", "TU_VoteInfo", "Users")


@pytest.fixture
def client():
    from aurweb.asgi import app
    yield TestClient(app=app)


@pytest.fixture
def tu_user():
    tu_type = db.query(AccountType,
                       AccountType.AccountType == "Trusted User").first()
    yield db.create(User, Username="test_tu", Email="test_tu@example.org",
                    RealName="Test TU", Passwd="testPassword",
                    AccountType=tu_type)


@pytest.fixture
def user():
    user_type = db.query(AccountType,
                         AccountType.AccountType == "User").first()
    yield db.create(User, Username="test", Email="test@example.org",
                    RealName="Test User", Passwd="testPassword",
                    AccountType=user_type)


def test_tu_index_guest(client):
    with client as request:
        response = request.get("/tu", allow_redirects=False)
    assert response.status_code == int(HTTPStatus.SEE_OTHER)
    assert response.headers.get("location") == "/"


def test_tu_index_unauthorized(client, user):
    cookies = {"AURSID": user.login(Request(), "testPassword")}
    with client as request:
        # Login as a normal user, not a TU.
        response = request.get("/tu", cookies=cookies, allow_redirects=False)
    assert response.status_code == int(HTTPStatus.SEE_OTHER)
    assert response.headers.get("location") == "/"


def test_tu_empty_index(client, tu_user):
    """ Check an empty index when we don't create any records. """

    # Make a default get request to /tu.
    cookies = {"AURSID": tu_user.login(Request(), "testPassword")}
    with client as request:
        response = request.get("/tu", cookies=cookies, allow_redirects=False)
    assert response.status_code == int(HTTPStatus.OK)

    # Parse lxml root.
    root = parse_root(response.text)

    # Check that .current-votes does not exist.
    tables = root.xpath('//table[contains(@class, "current-votes")]')
    assert len(tables) == 0

    # Check that .past-votes has does not exist.
    tables = root.xpath('//table[contains(@class, "current-votes")]')
    assert len(tables) == 0


def test_tu_index(client, tu_user):
    ts = int(datetime.utcnow().timestamp())

    # Create some test votes: (Agenda, Start, End).
    votes = [
        ("Test agenda 1", ts - 5, ts + 1000),  # Still running.
        ("Test agenda 2", ts - 1000, ts - 5)  # Not running anymore.
    ]
    vote_records = []
    for vote in votes:
        agenda, start, end = vote
        vote_records.append(
            db.create(TUVoteInfo, Agenda=agenda,
                      User=tu_user.Username,
                      Submitted=start, End=end,
                      Quorum=0.0,
                      Submitter=tu_user))

    # Vote on an ended proposal.
    vote_record = vote_records[1]
    vote_record.Yes += 1
    vote_record.ActiveTUs += 1
    db.create(TUVote, VoteInfo=vote_record, User=tu_user)

    cookies = {"AURSID": tu_user.login(Request(), "testPassword")}
    with client as request:
        # Pass an invalid cby and pby; let them default to "desc".
        response = request.get("/tu", cookies=cookies, params={
            "cby": "BAD!",
            "pby": "blah"
        }, allow_redirects=False)

    assert response.status_code == int(HTTPStatus.OK)

    # Rows we expect to exist in HTML produced by /tu for current votes.
    expected_rows = [
        (
            r'Test agenda 1',
            DATETIME_REGEX,
            DATETIME_REGEX,
            tu_user.Username,
            r'^(Yes|No)$'
        )
    ]

    # Assert that we are matching the number of current votes.
    current_votes = [c for c in votes if c[2] > ts]
    assert len(current_votes) == len(expected_rows)

    # Parse lxml.etree root.
    root = parse_root(response.text)

    table = get_table(root, "current-votes")
    rows = get_table_rows(table)
    for i, row in enumerate(rows):
        assert_current_vote_html(row, expected_rows[i])

    # Assert that we are matching the number of past votes.
    past_votes = [c for c in votes if c[2] <= ts]
    assert len(past_votes) == len(expected_rows)

    # Rows we expect to exist in HTML produced by /tu for past votes.
    expected_rows = [
        (
            r'Test agenda 2',
            DATETIME_REGEX,
            DATETIME_REGEX,
            tu_user.Username,
            r'^\d+$',
            r'^\d+$',
            r'^(Yes|No)$'
        )
    ]

    table = get_table(root, "past-votes")
    rows = get_table_rows(table)
    for i, row in enumerate(rows):
        assert_past_vote_html(row, expected_rows[i])

    # Get the .last-votes table and check that our vote shows up.
    table = get_table(root, "last-votes")
    rows = get_table_rows(table)
    assert len(rows) == 1

    # Check to see the rows match up to our user and related vote.
    username, vote_id = rows[0]
    vote_id = vote_id.xpath("./a")[0]
    assert username.text.strip() == tu_user.Username
    assert int(vote_id.text.strip()) == vote_records[1].ID


def test_tu_index_table_paging(client, tu_user):
    ts = int(datetime.utcnow().timestamp())

    for i in range(25):
        # Create 25 current votes.
        db.create(TUVoteInfo, Agenda=f"Agenda #{i}",
                  User=tu_user.Username,
                  Submitted=(ts - 5), End=(ts + 1000),
                  Quorum=0.0,
                  Submitter=tu_user, autocommit=False)

    for i in range(25):
        # Create 25 past votes.
        db.create(TUVoteInfo, Agenda=f"Agenda #{25 + i}",
                  User=tu_user.Username,
                  Submitted=(ts - 1000), End=(ts - 5),
                  Quorum=0.0,
                  Submitter=tu_user, autocommit=False)
    db.commit()

    cookies = {"AURSID": tu_user.login(Request(), "testPassword")}
    with client as request:
        response = request.get("/tu", cookies=cookies, allow_redirects=False)
    assert response.status_code == int(HTTPStatus.OK)

    # Parse lxml.etree root.
    root = parse_root(response.text)

    table = get_table(root, "current-votes")
    rows = get_table_rows(table)
    assert len(rows) == 10

    def make_expectation(offset, i):
        return [
            f"Agenda #{offset + i}",
            DATETIME_REGEX,
            DATETIME_REGEX,
            tu_user.Username,
            r'^(Yes|No)$'
        ]

    for i, row in enumerate(rows):
        assert_current_vote_html(row, make_expectation(0, i))

    # Parse out Back/Next buttons.
    directions = get_pkglist_directions(table)
    assert len(directions) == 1
    assert "Next" in directions[0].text

    # Now, get the next page of current votes.
    offset = 10  # Specify coff=10
    with client as request:
        response = request.get("/tu", cookies=cookies, params={
            "coff": offset
        }, allow_redirects=False)
    assert response.status_code == int(HTTPStatus.OK)

    old_rows = rows
    root = parse_root(response.text)

    table = get_table(root, "current-votes")
    rows = get_table_rows(table)
    assert rows != old_rows

    for i, row in enumerate(rows):
        assert_current_vote_html(row, make_expectation(offset, i))

    # Parse out Back/Next buttons.
    directions = get_pkglist_directions(table)
    assert len(directions) == 2
    assert "Back" in directions[0].text
    assert "Next" in directions[1].text

    # Make sure past-votes' Back/Next were not affected.
    past_votes = get_table(root, "past-votes")
    past_directions = get_pkglist_directions(past_votes)
    assert len(past_directions) == 1
    assert "Next" in past_directions[0].text

    offset = 20  # Specify coff=10
    with client as request:
        response = request.get("/tu", cookies=cookies, params={
            "coff": offset
        }, allow_redirects=False)
    assert response.status_code == int(HTTPStatus.OK)

    # Do it again, we only have five left.
    old_rows = rows
    root = parse_root(response.text)

    table = get_table(root, "current-votes")
    rows = get_table_rows(table)
    assert rows != old_rows
    for i, row in enumerate(rows):
        assert_current_vote_html(row, make_expectation(offset, i))

    # Parse out Back/Next buttons.
    directions = get_pkglist_directions(table)
    assert len(directions) == 1
    assert "Back" in directions[0].text

    # Make sure past-votes' Back/Next were not affected.
    past_votes = get_table(root, "past-votes")
    past_directions = get_pkglist_directions(past_votes)
    assert len(past_directions) == 1
    assert "Next" in past_directions[0].text


def test_tu_index_sorting(client, tu_user):
    ts = int(datetime.utcnow().timestamp())

    for i in range(2):
        # Create 'Agenda #1' and 'Agenda #2'.
        db.create(TUVoteInfo, Agenda=f"Agenda #{i + 1}",
                  User=tu_user.Username,
                  Submitted=(ts + 5), End=(ts + 1000),
                  Quorum=0.0,
                  Submitter=tu_user, autocommit=False)

        # Let's order each vote one day after the other.
        # This will allow us to test the sorting nature
        # of the tables.
        ts += 86405

    # Make a default request to /tu.
    cookies = {"AURSID": tu_user.login(Request(), "testPassword")}
    with client as request:
        response = request.get("/tu", cookies=cookies, allow_redirects=False)
    assert response.status_code == int(HTTPStatus.OK)

    # Get lxml handles of the document.
    root = parse_root(response.text)
    table = get_table(root, "current-votes")
    rows = get_table_rows(table)

    # The latest Agenda is at the top by default.
    expected = [
        "Agenda #2",
        "Agenda #1"
    ]

    assert len(rows) == len(expected)
    for i, row in enumerate(rows):
        assert_current_vote_html(row, [
            expected[i],
            DATETIME_REGEX,
            DATETIME_REGEX,
            tu_user.Username,
            r'^(Yes|No)$'
        ])

    # Make another request; one that sorts the current votes
    # in ascending order instead of the default descending order.
    with client as request:
        response = request.get("/tu", cookies=cookies, params={
            "cby": "asc"
        }, allow_redirects=False)
    assert response.status_code == int(HTTPStatus.OK)

    # Get lxml handles of the document.
    root = parse_root(response.text)
    table = get_table(root, "current-votes")
    rows = get_table_rows(table)

    # Reverse our expectations and assert that the proposals got flipped.
    rev_expected = list(reversed(expected))
    assert len(rows) == len(rev_expected)
    for i, row in enumerate(rows):
        assert_current_vote_html(row, [
            rev_expected[i],
            DATETIME_REGEX,
            DATETIME_REGEX,
            tu_user.Username,
            r'^(Yes|No)$'
        ])


def test_tu_index_last_votes(client, tu_user, user):
    ts = int(datetime.utcnow().timestamp())

    # Create a proposal which has ended.
    voteinfo = db.create(TUVoteInfo, Agenda="Test agenda",
                         User=user.Username,
                         Submitted=(ts - 1000),
                         End=(ts - 5),
                         Yes=1,
                         ActiveTUs=1,
                         Quorum=0.0,
                         Submitter=tu_user)

    # Create a vote on it from tu_user.
    db.create(TUVote, VoteInfo=voteinfo, User=tu_user)

    # Now, check that tu_user got populated in the .last-votes table.
    cookies = {"AURSID": tu_user.login(Request(), "testPassword")}
    with client as request:
        response = request.get("/tu", cookies=cookies)
    assert response.status_code == int(HTTPStatus.OK)

    root = parse_root(response.text)
    table = get_table(root, "last-votes")
    rows = get_table_rows(table)
    assert len(rows) == 1

    last_vote = rows[0]
    user, vote_id = last_vote.xpath("./td")
    vote_id = vote_id.xpath("./a")[0]

    assert user.text.strip() == tu_user.Username
    assert int(vote_id.text.strip()) == voteinfo.ID
