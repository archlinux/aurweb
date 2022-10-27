from typing import Tuple

import pytest

from aurweb import config, db, time
from aurweb.models import TUVote, TUVoteInfo, User
from aurweb.models.account_type import TRUSTED_USER_ID
from aurweb.scripts import tuvotereminder as reminder
from aurweb.testing.email import Email

aur_location = config.get("options", "aur_location")


def create_vote(user: User, voteinfo: TUVoteInfo) -> TUVote:
    with db.begin():
        vote = db.create(TUVote, User=user, VoteID=voteinfo.ID)
    return vote


def create_user(username: str, type_id: int):
    with db.begin():
        user = db.create(
            User,
            AccountTypeID=type_id,
            Username=username,
            Email=f"{username}@example.org",
            Passwd=str(),
        )
    return user


def email_pieces(voteinfo: TUVoteInfo) -> Tuple[str, str]:
    """
    Return a (subject, content) tuple based on voteinfo.ID

    :param voteinfo: TUVoteInfo instance
    :return: tuple(subject, content)
    """
    subject = f"TU Vote Reminder: Proposal {voteinfo.ID}"
    content = (
        f"Please remember to cast your vote on proposal {voteinfo.ID} "
        f"[1]. The voting period\nends in less than 48 hours.\n\n"
        f"[1] {aur_location}/tu/?id={voteinfo.ID}"
    )
    return subject, content


@pytest.fixture
def user(db_test) -> User:
    yield create_user("test", TRUSTED_USER_ID)


@pytest.fixture
def user2() -> User:
    yield create_user("test2", TRUSTED_USER_ID)


@pytest.fixture
def user3() -> User:
    yield create_user("test3", TRUSTED_USER_ID)


@pytest.fixture
def voteinfo(user: User) -> TUVoteInfo:
    now = time.utcnow()
    start = config.getint("tuvotereminder", "range_start")
    with db.begin():
        voteinfo = db.create(
            TUVoteInfo,
            Agenda="Lorem ipsum.",
            User=user.Username,
            End=(now + start + 1),
            Quorum=0.00,
            Submitter=user,
            Submitted=0,
        )
    yield voteinfo


def test_tu_vote_reminders(user: User, user2: User, user3: User, voteinfo: TUVoteInfo):
    reminder.main()
    assert Email.count() == 3

    emails = [Email(i).parse() for i in range(1, 4)]
    subject, content = email_pieces(voteinfo)
    expectations = [
        # (to, content)
        (user.Email, subject, content),
        (user2.Email, subject, content),
        (user3.Email, subject, content),
    ]
    for i, element in enumerate(expectations):
        email, subject, content = element
        assert emails[i].headers.get("To") == email
        assert emails[i].headers.get("Subject") == subject
        assert emails[i].body == content


def test_tu_vote_reminders_only_unvoted(
    user: User, user2: User, user3: User, voteinfo: TUVoteInfo
):
    # Vote with user2 and user3; leaving only user to be notified.
    create_vote(user2, voteinfo)
    create_vote(user3, voteinfo)

    reminder.main()
    assert Email.count() == 1

    email = Email(1).parse()
    assert email.headers.get("To") == user.Email

    subject, content = email_pieces(voteinfo)
    assert email.headers.get("Subject") == subject
    assert email.body == content
