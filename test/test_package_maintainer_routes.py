import re
from http import HTTPStatus
from io import StringIO
from typing import Tuple

import lxml.etree
import pytest
from fastapi.testclient import TestClient

from aurweb import config, db, filters, time
from aurweb.models.account_type import DEVELOPER_ID, PACKAGE_MAINTAINER_ID, AccountType
from aurweb.models.user import User
from aurweb.models.vote import Vote
from aurweb.models.voteinfo import VoteInfo
from aurweb.testing.requests import Request

DATETIME_REGEX = r"^[0-9]{4}-[0-9]{2}-[0-9]{2} \(.+\)$"
PARTICIPATION_REGEX = r"^1?[0-9]{2}[%]$"  # 0% - 100%


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
    return node.xpath("./a")[0].text.strip()


def get_span(node):
    return node.xpath("./span")[0].text.strip()


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
def setup(db_test):
    return


@pytest.fixture
def client():
    from aurweb.asgi import app

    client = TestClient(app=app)

    # disable redirects for our tests
    client.follow_redirects = False
    yield client


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
def pm_user2():
    with db.begin():
        pm_user2 = db.create(
            User,
            Username="test_pm2",
            Email="test_pm2@example.org",
            RealName="Test PM 2",
            Passwd="testPassword",
            AccountTypeID=PACKAGE_MAINTAINER_ID,
        )
    yield pm_user2


@pytest.fixture
def user():
    user_type = db.query(AccountType, AccountType.AccountType == "User").first()
    with db.begin():
        user = db.create(
            User,
            Username="test",
            Email="test@example.org",
            RealName="Test User",
            Passwd="testPassword",
            AccountType=user_type,
        )
    yield user


@pytest.fixture
def proposal(user, pm_user):
    ts = time.utcnow()
    agenda = "Test proposal."
    start = ts - 5
    end = ts + 1000

    with db.begin():
        voteinfo = db.create(
            VoteInfo,
            Agenda=agenda,
            Quorum=0.0,
            User=user.Username,
            Submitter=pm_user,
            Submitted=start,
            End=end,
        )
    yield (pm_user, user, voteinfo)


def test_pm_index_guest(client):
    headers = {"referer": config.get("options", "aur_location") + "/package-maintainer"}
    with client as request:
        response = request.get("/package-maintainer", headers=headers)
    assert response.status_code == int(HTTPStatus.SEE_OTHER)

    params = filters.urlencode({"next": "/package-maintainer"})
    assert response.headers.get("location") == f"/login?{params}"


def test_pm_index_unauthorized(client: TestClient, user: User):
    cookies = {"AURSID": user.login(Request(), "testPassword")}
    with client as request:
        # Login as a normal user, not a TU.
        request.cookies = cookies
        response = request.get("/package-maintainer")
    assert response.status_code == int(HTTPStatus.SEE_OTHER)
    assert response.headers.get("location") == "/"


def test_pm_empty_index(client, pm_user):
    """Check an empty index when we don't create any records."""

    # Make a default get request to /package-maintainer.
    cookies = {"AURSID": pm_user.login(Request(), "testPassword")}
    with client as request:
        request.cookies = cookies
        response = request.get("/package-maintainer")
    assert response.status_code == int(HTTPStatus.OK)

    # Parse lxml root.
    root = parse_root(response.text)

    # Check that .current-votes does not exist.
    tables = root.xpath('//table[contains(@class, "current-votes")]')
    assert len(tables) == 0

    # Check that .past-votes has does not exist.
    tables = root.xpath('//table[contains(@class, "current-votes")]')
    assert len(tables) == 0


def test_pm_index(client, pm_user):
    ts = time.utcnow()

    # Create some test votes: (Agenda, Start, End).
    votes = [
        ("Test agenda 1", ts - 5, ts + 1000),  # Still running.
        ("Test agenda 2", ts - 1000, ts - 5),  # Not running anymore.
    ]
    vote_records = []
    with db.begin():
        for vote in votes:
            agenda, start, end = vote
            vote_records.append(
                db.create(
                    VoteInfo,
                    Agenda=agenda,
                    User=pm_user.Username,
                    Submitted=start,
                    End=end,
                    Quorum=0.0,
                    Submitter=pm_user,
                )
            )

    with db.begin():
        # Vote on an ended proposal.
        vote_record = vote_records[1]
        vote_record.Yes += 1
        vote_record.ActiveUsers += 1
        db.create(Vote, VoteInfo=vote_record, User=pm_user)

    cookies = {"AURSID": pm_user.login(Request(), "testPassword")}
    with client as request:
        # Pass an invalid cby and pby; let them default to "desc".
        request.cookies = cookies
        response = request.get(
            "/package-maintainer",
            params={"cby": "BAD!", "pby": "blah"},
        )

    assert response.status_code == int(HTTPStatus.OK)

    # Rows we expect to exist in HTML produced by /package-maintainer for current votes.
    expected_rows = [
        (
            r"Test agenda 1",
            DATETIME_REGEX,
            DATETIME_REGEX,
            pm_user.Username,
            r"^(Yes|No)$",
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

    # Rows we expect to exist in HTML produced by /package-maintainer for past votes.
    expected_rows = [
        (
            r"Test agenda 2",
            DATETIME_REGEX,
            DATETIME_REGEX,
            pm_user.Username,
            r"^\d+$",
            r"^\d+$",
            r"^(Yes|No)$",
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
    username = username.xpath("./a")[0]
    vote_id = vote_id.xpath("./a")[0]
    assert username.text.strip() == pm_user.Username
    assert int(vote_id.text.strip()) == vote_records[1].ID


def test_pm_stats(client: TestClient, pm_user: User):
    cookies = {"AURSID": pm_user.login(Request(), "testPassword")}
    with client as request:
        request.cookies = cookies
        response = request.get("/package-maintainer")
    assert response.status_code == HTTPStatus.OK

    root = parse_root(response.text)
    stats = root.xpath('//table[@class="no-width"]')[0]
    rows = stats.xpath("./tbody/tr")

    # We have one package maintainer.
    total = rows[0]
    label, count = total.xpath("./td")
    assert int(count.text.strip()) == 1

    # And we have one active PM.
    active = rows[1]
    label, count = active.xpath("./td")
    assert int(count.text.strip()) == 1

    with db.begin():
        pm_user.InactivityTS = time.utcnow()

    with client as request:
        request.cookies = cookies
        response = request.get("/package-maintainer")
    assert response.status_code == HTTPStatus.OK

    root = parse_root(response.text)
    stats = root.xpath('//table[@class="no-width"]')[0]
    rows = stats.xpath("./tbody/tr")

    # We have one package maintainer.
    total = rows[0]
    label, count = total.xpath("./td")
    assert int(count.text.strip()) == 1

    # But we have no more active PMs.
    active = rows[1]
    label, count = active.xpath("./td")
    assert int(count.text.strip()) == 0


def test_pm_index_table_paging(client, pm_user):
    ts = time.utcnow()

    with db.begin():
        for i in range(25):
            # Create 25 current votes.
            db.create(
                VoteInfo,
                Agenda=f"Agenda #{i}",
                User=pm_user.Username,
                Submitted=(ts - 5),
                End=(ts + 1000),
                Quorum=0.0,
                Submitter=pm_user,
            )

        for i in range(25):
            # Create 25 past votes.
            db.create(
                VoteInfo,
                Agenda=f"Agenda #{25 + i}",
                User=pm_user.Username,
                Submitted=(ts - 1000),
                End=(ts - 5),
                Quorum=0.0,
                Submitter=pm_user,
            )

    cookies = {"AURSID": pm_user.login(Request(), "testPassword")}
    with client as request:
        request.cookies = cookies
        response = request.get("/package-maintainer")
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
            pm_user.Username,
            r"^(Yes|No)$",
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
        request.cookies = cookies
        response = request.get("package-maintainer", params={"coff": offset})
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
        request.cookies = cookies
        response = request.get("/package-maintainer", params={"coff": offset})
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


def test_pm_index_sorting(client, pm_user):
    ts = time.utcnow()

    with db.begin():
        for i in range(2):
            # Create 'Agenda #1' and 'Agenda #2'.
            db.create(
                VoteInfo,
                Agenda=f"Agenda #{i + 1}",
                User=pm_user.Username,
                Submitted=(ts + 5),
                End=(ts + 1000),
                Quorum=0.0,
                Submitter=pm_user,
            )

            # Let's order each vote one day after the other.
            # This will allow us to test the sorting nature
            # of the tables.
            ts += 86405

    # Make a default request to /package-maintainer.
    cookies = {"AURSID": pm_user.login(Request(), "testPassword")}
    with client as request:
        request.cookies = cookies
        response = request.get("/package-maintainer")
    assert response.status_code == int(HTTPStatus.OK)

    # Get lxml handles of the document.
    root = parse_root(response.text)
    table = get_table(root, "current-votes")
    rows = get_table_rows(table)

    # The latest Agenda is at the top by default.
    expected = ["Agenda #2", "Agenda #1"]

    assert len(rows) == len(expected)
    for i, row in enumerate(rows):
        assert_current_vote_html(
            row,
            [
                expected[i],
                DATETIME_REGEX,
                DATETIME_REGEX,
                pm_user.Username,
                r"^(Yes|No)$",
            ],
        )

    # Make another request; one that sorts the current votes
    # in ascending order instead of the default descending order.
    with client as request:
        request.cookies = cookies
        response = request.get("/package-maintainer", params={"cby": "asc"})
    assert response.status_code == int(HTTPStatus.OK)

    # Get lxml handles of the document.
    root = parse_root(response.text)
    table = get_table(root, "current-votes")
    rows = get_table_rows(table)

    # Reverse our expectations and assert that the proposals got flipped.
    rev_expected = list(reversed(expected))
    assert len(rows) == len(rev_expected)
    for i, row in enumerate(rows):
        assert_current_vote_html(
            row,
            [
                rev_expected[i],
                DATETIME_REGEX,
                DATETIME_REGEX,
                pm_user.Username,
                r"^(Yes|No)$",
            ],
        )


def test_pm_index_last_votes(
    client: TestClient, pm_user: User, pm_user2: User, user: User
):
    ts = time.utcnow()

    with db.begin():
        # Create a proposal which has ended.
        voteinfo = db.create(
            VoteInfo,
            Agenda="Test agenda",
            User=user.Username,
            Submitted=(ts - 1000),
            End=(ts - 5),
            Yes=1,
            No=1,
            ActiveUsers=1,
            Quorum=0.0,
            Submitter=pm_user,
        )

        # Create a vote on it from pm_user.
        db.create(Vote, VoteInfo=voteinfo, User=pm_user)
        db.create(Vote, VoteInfo=voteinfo, User=pm_user2)

    # Now, check that pm_user got populated in the .last-votes table.
    cookies = {"AURSID": pm_user.login(Request(), "testPassword")}
    with client as request:
        request.cookies = cookies
        response = request.get("/package-maintainer")
    assert response.status_code == int(HTTPStatus.OK)

    root = parse_root(response.text)
    table = get_table(root, "last-votes")
    rows = get_table_rows(table)
    assert len(rows) == 2

    last_vote = rows[0]
    user, vote_id = last_vote.xpath("./td/a")
    assert user.text.strip() == pm_user.Username
    assert int(vote_id.text.strip()) == voteinfo.ID

    last_vote = rows[1]
    user, vote_id = last_vote.xpath("./td/a")
    assert int(vote_id.text.strip()) == voteinfo.ID
    assert user.text.strip() == pm_user2.Username


def test_pm_proposal_not_found(client, pm_user):
    cookies = {"AURSID": pm_user.login(Request(), "testPassword")}
    with client as request:
        request.cookies = cookies
        response = request.get(
            "/package-maintainer", params={"id": 1}, follow_redirects=True
        )
    assert response.status_code == int(HTTPStatus.NOT_FOUND)


def test_pm_proposal_unauthorized(
    client: TestClient, user: User, proposal: Tuple[User, User, VoteInfo]
):
    cookies = {"AURSID": user.login(Request(), "testPassword")}
    endpoint = f"/package-maintainer/{proposal[2].ID}"
    with client as request:
        request.cookies = cookies
        response = request.get(endpoint)
    assert response.status_code == int(HTTPStatus.SEE_OTHER)
    assert response.headers.get("location") == "/package-maintainer"

    with client as request:
        request.cookies = cookies
        response = request.post(endpoint, data={"decision": False})
    assert response.status_code == int(HTTPStatus.SEE_OTHER)
    assert response.headers.get("location") == "/package-maintainer"


def test_pm_running_proposal(client: TestClient, proposal: Tuple[User, User, VoteInfo]):
    pm_user, user, voteinfo = proposal
    with db.begin():
        voteinfo.ActiveUsers = 1

    # Initiate an authenticated GET request to /package-maintainer/{proposal_id}.
    proposal_id = voteinfo.ID
    cookies = {"AURSID": pm_user.login(Request(), "testPassword")}
    with client as request:
        request.cookies = cookies
        response = request.get(f"/package-maintainer/{proposal_id}")
    assert response.status_code == int(HTTPStatus.OK)

    # Alright, now let's continue on to verifying some markup.
    # First, let's verify that the proposal details match.
    root = parse_root(response.text)
    details = root.xpath('//div[@class="proposal details"]')[0]

    vote_running = root.xpath('//p[contains(@class, "vote-running")]')[0]
    assert vote_running.text.strip() == "This vote is still running."

    # Verify User field.
    username = details.xpath('./div[contains(@class, "user")]/strong/a/text()')[0]
    assert username.strip() == user.Username

    active = details.xpath('./div[contains(@class, "field")]')[1]
    content = active.text.strip()
    assert "Active Package Maintainers assigned:" in content
    assert "1" in content

    submitted = details.xpath('./div[contains(@class, "submitted")]/text()')[0]
    assert (
        re.match(
            r"^Submitted: \d{4}-\d{2}-\d{2} \d{2}:\d{2} \(.+\) by$", submitted.strip()
        )
        is not None
    )
    submitter = details.xpath('./div[contains(@class, "submitted")]/a')[0]
    assert submitter.text.strip() == pm_user.Username
    assert submitter.attrib["href"] == f"/account/{pm_user.Username}"

    end = details.xpath('./div[contains(@class, "end")]')[0]
    end_label = end.xpath("./text()")[0]
    assert end_label.strip() == "End:"

    end_datetime = end.xpath("./strong/text()")[0]
    assert (
        re.match(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2} \(.+\)$", end_datetime.strip())
        is not None
    )

    # We have not voted yet. Assert that our voting form is shown.
    form = root.xpath('//form[contains(@class, "action-form")]')[0]
    fields = form.xpath("./fieldset")[0]
    buttons = fields.xpath('./button[@name="decision"]')
    assert len(buttons) == 3

    # Check the button names and values.
    yes, no, abstain = buttons

    # Yes
    assert yes.attrib["name"] == "decision"
    assert yes.attrib["value"] == "Yes"

    # No
    assert no.attrib["name"] == "decision"
    assert no.attrib["value"] == "No"

    # Abstain
    assert abstain.attrib["name"] == "decision"
    assert abstain.attrib["value"] == "Abstain"

    # Create a vote.
    with db.begin():
        db.create(Vote, VoteInfo=voteinfo, User=pm_user)
        voteinfo.ActiveUsers += 1
        voteinfo.Yes += 1

    # Make another request now that we've voted.
    with client as request:
        request.cookies = cookies
        response = request.get(
            "/package-maintainer", params={"id": voteinfo.ID}, follow_redirects=True
        )
    assert response.status_code == int(HTTPStatus.OK)

    # Parse our new root.
    root = parse_root(response.text)

    # Check that we no longer have a voting form.
    form = root.xpath('//form[contains(@class, "action-form")]')
    assert not form

    # Check that we're told we've voted.
    status = root.xpath('//span[contains(@class, "status")]/text()')[0]
    assert status == "You've already voted for this proposal."


def test_pm_ended_proposal(client, proposal):
    pm_user, user, voteinfo = proposal

    ts = time.utcnow()
    with db.begin():
        voteinfo.End = ts - 5  # 5 seconds ago.

    # Initiate an authenticated GET request to /package-maintainer/{proposal_id}.
    proposal_id = voteinfo.ID
    cookies = {"AURSID": pm_user.login(Request(), "testPassword")}
    with client as request:
        request.cookies = cookies
        response = request.get(f"/package-maintainer/{proposal_id}")
    assert response.status_code == int(HTTPStatus.OK)

    # Alright, now let's continue on to verifying some markup.
    # First, let's verify that the proposal details match.
    root = parse_root(response.text)
    details = root.xpath('//div[@class="proposal details"]')[0]

    vote_running = root.xpath('//p[contains(@class, "vote-running")]')
    assert not vote_running

    result_node = details.xpath('./div[contains(@class, "result")]')[0]
    result_label = result_node.xpath("./text()")[0]
    assert result_label.strip() == "Result:"

    result = result_node.xpath("./span/text()")[0]
    assert result.strip() == "unknown"

    # Check that voting has ended.
    form = root.xpath('//form[contains(@class, "action-form")]')
    assert not form

    # We should see a status about it.
    status = root.xpath('//span[contains(@class, "status")]/text()')[0]
    assert status == "Voting is closed for this proposal."


def test_pm_proposal_vote_not_found(client, pm_user):
    """Test POST request to a missing vote."""
    cookies = {"AURSID": pm_user.login(Request(), "testPassword")}
    with client as request:
        data = {"decision": "Yes"}
        request.cookies = cookies
        response = request.post("/package-maintainer/1", data=data)
    assert response.status_code == int(HTTPStatus.NOT_FOUND)


def test_pm_proposal_vote(client, proposal):
    pm_user, user, voteinfo = proposal

    # Store the current related values.
    yes = voteinfo.Yes

    cookies = {"AURSID": pm_user.login(Request(), "testPassword")}
    with client as request:
        data = {"decision": "Yes"}
        request.cookies = cookies
        response = request.post(f"/package-maintainer/{voteinfo.ID}", data=data)
    assert response.status_code == int(HTTPStatus.OK)

    # Check that the proposal record got updated.
    db.refresh(voteinfo)
    assert voteinfo.Yes == yes + 1

    # Check that the new PMVote exists.
    vote = db.query(Vote, Vote.VoteInfo == voteinfo, Vote.User == pm_user).first()
    assert vote is not None

    root = parse_root(response.text)

    # Check that we're told we've voted.
    status = root.xpath('//span[contains(@class, "status")]/text()')[0]
    assert status == "You've already voted for this proposal."


def test_pm_proposal_vote_unauthorized(
    client: TestClient, proposal: Tuple[User, User, VoteInfo]
):
    pm_user, user, voteinfo = proposal

    with db.begin():
        pm_user.AccountTypeID = DEVELOPER_ID

    cookies = {"AURSID": pm_user.login(Request(), "testPassword")}
    with client as request:
        data = {"decision": "Yes"}
        request.cookies = cookies
        response = request.post(f"package-maintainer/{voteinfo.ID}", data=data)
    assert response.status_code == int(HTTPStatus.UNAUTHORIZED)

    root = parse_root(response.text)
    status = root.xpath('//span[contains(@class, "status")]/text()')[0]
    assert status == "Only Package Maintainers are allowed to vote."

    with client as request:
        data = {"decision": "Yes"}
        request.cookies = cookies
        response = request.get(f"/package-maintainer/{voteinfo.ID}", params=data)
    assert response.status_code == int(HTTPStatus.OK)

    root = parse_root(response.text)
    status = root.xpath('//span[contains(@class, "status")]/text()')[0]
    assert status == "Only Package Maintainers are allowed to vote."


def test_pm_proposal_vote_cant_self_vote(client, proposal):
    pm_user, user, voteinfo = proposal

    # Update voteinfo.User.
    with db.begin():
        voteinfo.User = pm_user.Username

    cookies = {"AURSID": pm_user.login(Request(), "testPassword")}
    with client as request:
        data = {"decision": "Yes"}
        request.cookies = cookies
        response = request.post(f"/package-maintainer/{voteinfo.ID}", data=data)
    assert response.status_code == int(HTTPStatus.BAD_REQUEST)

    root = parse_root(response.text)
    status = root.xpath('//span[contains(@class, "status")]/text()')[0]
    assert status == "You cannot vote in an proposal about you."

    with client as request:
        data = {"decision": "Yes"}
        request.cookies = cookies
        response = request.get(f"/package-maintainer/{voteinfo.ID}", params=data)
    assert response.status_code == int(HTTPStatus.OK)

    root = parse_root(response.text)
    status = root.xpath('//span[contains(@class, "status")]/text()')[0]
    assert status == "You cannot vote in an proposal about you."


def test_pm_proposal_vote_already_voted(client, proposal):
    pm_user, user, voteinfo = proposal

    with db.begin():
        db.create(Vote, VoteInfo=voteinfo, User=pm_user)
        voteinfo.Yes += 1
        voteinfo.ActiveUsers += 1

    cookies = {"AURSID": pm_user.login(Request(), "testPassword")}
    with client as request:
        data = {"decision": "Yes"}
        request.cookies = cookies
        response = request.post(f"/package-maintainer/{voteinfo.ID}", data=data)
    assert response.status_code == int(HTTPStatus.BAD_REQUEST)

    root = parse_root(response.text)
    status = root.xpath('//span[contains(@class, "status")]/text()')[0]
    assert status == "You've already voted for this proposal."

    with client as request:
        data = {"decision": "Yes"}
        request.cookies = cookies
        response = request.get(f"/package-maintainer/{voteinfo.ID}", params=data)
    assert response.status_code == int(HTTPStatus.OK)

    root = parse_root(response.text)
    status = root.xpath('//span[contains(@class, "status")]/text()')[0]
    assert status == "You've already voted for this proposal."


def test_pm_proposal_vote_invalid_decision(client, proposal):
    pm_user, user, voteinfo = proposal

    cookies = {"AURSID": pm_user.login(Request(), "testPassword")}
    with client as request:
        data = {"decision": "EVIL"}
        request.cookies = cookies
        response = request.post(f"package-maintainer/{voteinfo.ID}", data=data)
    assert response.status_code == int(HTTPStatus.BAD_REQUEST)
    assert response.text == "Invalid 'decision' value."


def test_pm_addvote(client: TestClient, pm_user: User):
    cookies = {"AURSID": pm_user.login(Request(), "testPassword")}
    with client as request:
        request.cookies = cookies
        response = request.get("/addvote")
    assert response.status_code == int(HTTPStatus.OK)


def test_pm_addvote_unauthorized(
    client: TestClient, user: User, proposal: Tuple[User, User, VoteInfo]
):
    cookies = {"AURSID": user.login(Request(), "testPassword")}
    with client as request:
        request.cookies = cookies
        response = request.get("/addvote")
    assert response.status_code == int(HTTPStatus.SEE_OTHER)
    assert response.headers.get("location") == "/package-maintainer"

    with client as request:
        request.cookies = cookies
        response = request.post("/addvote")
    assert response.status_code == int(HTTPStatus.SEE_OTHER)
    assert response.headers.get("location") == "/package-maintainer"


def test_pm_addvote_invalid_type(client: TestClient, pm_user: User):
    cookies = {"AURSID": pm_user.login(Request(), "testPassword")}
    with client as request:
        request.cookies = cookies
        response = request.get("/addvote", params={"type": "faketype"})
    assert response.status_code == int(HTTPStatus.OK)

    root = parse_root(response.text)
    error = root.xpath('//*[contains(@class, "error")]/text()')[0]
    assert error.strip() == "Invalid type."


def test_pm_addvote_post(client: TestClient, pm_user: User, user: User):
    cookies = {"AURSID": pm_user.login(Request(), "testPassword")}

    data = {"user": user.Username, "type": "add_pm", "agenda": "Blah"}

    with client as request:
        request.cookies = cookies
        response = request.post("/addvote", data=data)
    assert response.status_code == int(HTTPStatus.SEE_OTHER)

    voteinfo = db.query(VoteInfo, VoteInfo.Agenda == "Blah").first()
    assert voteinfo is not None


def test_pm_addvote_post_cant_duplicate_username(
    client: TestClient, pm_user: User, user: User
):
    cookies = {"AURSID": pm_user.login(Request(), "testPassword")}

    data = {"user": user.Username, "type": "add_pm", "agenda": "Blah"}

    with client as request:
        request.cookies = cookies
        response = request.post("/addvote", data=data)
    assert response.status_code == int(HTTPStatus.SEE_OTHER)

    voteinfo = db.query(VoteInfo, VoteInfo.Agenda == "Blah").first()
    assert voteinfo is not None

    with client as request:
        request.cookies = cookies
        response = request.post("/addvote", data=data)
    assert response.status_code == int(HTTPStatus.BAD_REQUEST)


def test_pm_addvote_post_invalid_username(client: TestClient, pm_user: User):
    cookies = {"AURSID": pm_user.login(Request(), "testPassword")}
    data = {"user": "fakeusername"}
    with client as request:
        request.cookies = cookies
        response = request.post("/addvote", data=data)
    assert response.status_code == int(HTTPStatus.NOT_FOUND)


def test_pm_addvote_post_invalid_type(client: TestClient, pm_user: User, user: User):
    cookies = {"AURSID": pm_user.login(Request(), "testPassword")}
    data = {"user": user.Username}
    with client as request:
        request.cookies = cookies
        response = request.post("/addvote", data=data)
    assert response.status_code == int(HTTPStatus.BAD_REQUEST)


def test_pm_addvote_post_invalid_agenda(client: TestClient, pm_user: User, user: User):
    cookies = {"AURSID": pm_user.login(Request(), "testPassword")}
    data = {"user": user.Username, "type": "add_pm"}
    with client as request:
        request.cookies = cookies
        response = request.post("/addvote", data=data)
    assert response.status_code == int(HTTPStatus.BAD_REQUEST)


def test_pm_addvote_post_bylaws(client: TestClient, pm_user: User):
    # Bylaws votes do not need a user specified.
    cookies = {"AURSID": pm_user.login(Request(), "testPassword")}
    data = {"type": "bylaws", "agenda": "Blah blah!"}
    with client as request:
        request.cookies = cookies
        response = request.post("/addvote", data=data)
    assert response.status_code == int(HTTPStatus.SEE_OTHER)
