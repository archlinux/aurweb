from collections.abc import Callable
from datetime import UTC, datetime, timedelta

import pytest

from aurweb import db
from aurweb.models import (
    PackageBase,
    PackageComaintainer,
    PackageComment,
    PackageNotification,
    PackageRequest,
    PackageVote,
    User,
    Vote,
    VoteInfo,
)
from aurweb.models.account_type import PACKAGE_MAINTAINER_ID, USER_ID
from aurweb.models.request_type import DELETION_ID
from aurweb.scripts import accountmaint
from aurweb.testing.email import Email

LIFETIME = 1209600
WARN_AFTER = 604800


@pytest.fixture(autouse=True)
def setup(db_test):
    return


def make_user(name: str, age: int, **kwargs) -> User:
    """An account registered `age` seconds ago, unverified unless told."""
    fields = {
        "Username": name,
        "Email": f"{name}@example.org",
        "Passwd": "testPassword",
        "AccountTypeID": USER_ID,
        "EmailVerified": 0,
        "RegistrationTS": datetime.now(UTC) - timedelta(seconds=age),
        **kwargs,
    }
    with db.begin():
        return db.create(User, **fields)


def usernames() -> set[str]:
    return {user.Username for user in db.query(User)}


def test_deletes_only_expired_unverified_accounts():
    make_user("stale", LIFETIME + 60)
    make_user("fresh", 60)
    make_user("verified", LIFETIME + 60, EmailVerified=1)

    assert accountmaint._main() == (0, 1)

    assert usernames() == {"fresh", "verified"}


def _ago(seconds: int) -> int:
    return int(datetime.now(UTC).timestamp()) - seconds


@pytest.mark.parametrize("field", ["LastLogin", "LastSSHLogin"])
def test_recently_authenticated_accounts_are_spared(field: str):
    """Someone still using the account keeps it, verified or not."""
    make_user("stale", LIFETIME + 60)
    make_user("used", LIFETIME + 60, **{field: _ago(60)})

    assert accountmaint._main() == (0, 1)

    assert usernames() == {"used"}


@pytest.mark.parametrize("field", ["LastLogin", "LastSSHLogin"])
def test_one_stale_login_does_not_buy_immunity(field: str):
    """A bot that logged in once at signup must not survive forever."""
    make_user("botlike", LIFETIME + 60, **{field: _ago(LIFETIME + 30)})

    assert accountmaint._main() == (0, 1)

    assert usernames() == set()


@pytest.mark.parametrize("field", ["LastLogin", "LastSSHLogin"])
def test_recently_authenticated_accounts_are_not_warned(field: str):
    make_user("used", WARN_AFTER + 60, **{field: _ago(60)})

    assert accountmaint._main() == (0, 0)

    assert Email.count() == 0


def test_suspension_is_not_a_reprieve():
    """A suspended account with nothing behind it still goes."""
    make_user("banned", LIFETIME + 60, Suspended=1)

    assert accountmaint._main() == (0, 1)

    assert usernames() == set()


def test_elevated_accounts_are_never_deleted():
    make_user("pm", LIFETIME + 60, AccountTypeID=PACKAGE_MAINTAINER_ID)

    accountmaint._main()

    assert usernames() == {"pm"}


def test_dry_run_reports_without_deleting():
    make_user("stale", LIFETIME + 60)

    assert accountmaint._main(dry_run=True) == (0, 1)
    assert usernames() == {"stale"}


def make_base(user: User) -> PackageBase:
    """Caller holds the transaction; nesting db.begin() would raise."""
    return db.create(PackageBase, Name=f"base-{user.ID}", Maintainer=user)


# Each entry attaches one kind of content to an otherwise-doomed account.
CONTENT: dict[str, Callable[[User], object]] = {
    "PackageBase.Maintainer": make_base,
    "PackageBase.Flagger": lambda u: db.create(
        PackageBase, Name=f"flagged-{u.ID}", Flagger=u
    ),
    "PackageComment": lambda u: db.create(
        PackageComment,
        PackageBase=make_base(u),
        User=u,
        Comments="x",
        RenderedComment="",
    ),
    "PackageVote": lambda u: db.create(
        PackageVote, User=u, PackageBase=make_base(u), VoteTS=1
    ),
    "PackageComaintainer": lambda u: db.create(
        PackageComaintainer, User=u, PackageBase=make_base(u), Priority=1
    ),
    "PackageRequest": lambda u: db.create(
        PackageRequest,
        ReqTypeID=DELETION_ID,
        PackageBase=make_base(u),
        PackageBaseName=f"base-{u.ID}",
        User=u,
        Comments="x",
        ClosureComment="",
    ),
    "PackageNotification": lambda u: db.create(
        PackageNotification, User=u, PackageBase=make_base(u)
    ),
    "VoteInfo": lambda u: db.create(
        VoteInfo,
        Agenda="x",
        User=u.Username,
        Submitted=1,
        End=2,
        Quorum=0,
        Submitter=u,
    ),
    "Vote": lambda u: db.create(
        Vote,
        VoteInfo=db.create(
            VoteInfo,
            Agenda="y",
            User=u.Username,
            Submitted=1,
            End=2,
            Quorum=0,
            Submitter=u,
        ),
        User=u,
    ),
}


@pytest.mark.parametrize("kind", list(CONTENT))
def test_content_spares_an_expired_account(kind: str):
    user = make_user("owner", LIFETIME + 60)
    with db.begin():
        CONTENT[kind](user)

    accountmaint._main()

    assert usernames() == {"owner"}, f"{kind} did not spare the account"


def test_warns_only_inside_the_band():
    make_user("just_in", WARN_AFTER + 60)
    make_user("just_out", WARN_AFTER + accountmaint._warning_window() + 60)
    make_user("nearly_out", WARN_AFTER + accountmaint._warning_window() - 60)
    make_user("too_young", WARN_AFTER - 60)

    assert accountmaint._main() == (2, 0)

    recipients = {Email(i).parse().headers["To"] for i in (1, 2)}
    assert recipients == {"just_in@example.org", "nearly_out@example.org"}
    email = Email(1).parse()
    assert email.headers["Subject"] == "AUR Account Pending Deletion"
    assert "will be deleted in 7 days" in email.body
    assert Email.count() == 2


def test_warning_is_not_repeated_on_a_second_run():
    """The live token left by the first mail suppresses the second."""
    make_user("stale", WARN_AFTER + 60)

    assert accountmaint._main() == (1, 0)
    assert Email.count() == 1

    assert accountmaint._main() == (0, 0)
    assert Email.count() == 1


def test_warning_resumes_once_the_token_lapses():
    user = make_user("stale", WARN_AFTER + 60)

    assert accountmaint._main() == (1, 0)

    # Expire the token the way time would.
    with db.begin():
        user.EmailVerificationExpiry = 1

    assert accountmaint._main() == (1, 0)
    assert Email.count() == 2


def test_warning_carries_a_live_token():
    """The registration token is long expired by the time we warn."""
    user = make_user("warned", WARN_AFTER + 60, EmailVerificationToken=None)

    accountmaint._main()

    db.get_session().refresh(user)
    assert user.EmailVerificationToken is not None
    assert f"/account/verify/{user.EmailVerificationToken}" in Email(1).parse().body


def test_suspended_accounts_are_not_warned():
    make_user("banned", WARN_AFTER + 60, Suspended=1)

    assert accountmaint._main() == (0, 0)
    assert Email.count() == 0


def test_content_owners_are_not_warned():
    user = make_user("owner", WARN_AFTER + 60)
    with db.begin():
        make_base(user)

    assert accountmaint._main() == (0, 0)
    assert Email.count() == 0


def test_dry_run_sends_no_mail():
    make_user("warned", WARN_AFTER + 60)

    assert accountmaint._main(dry_run=True) == (1, 0)
    assert Email.count() == 0


def test_deletes_across_batch_boundaries(monkeypatch):
    monkeypatch.setattr(accountmaint, "BATCH_SIZE", 2)
    for i in range(5):
        make_user(f"stale{i}", LIFETIME + 60)

    assert accountmaint._main() == (0, 5)
    assert usernames() == set()


def test_rejects_a_ttl_that_would_silence_every_warning(monkeypatch):
    """A signup token still live at the warning band warns nobody."""
    monkeypatch.setattr(accountmaint, "_warning_window", lambda: WARN_AFTER)

    with pytest.raises(accountmaint.ConfigError, match="email_verification_ttl"):
        accountmaint.check_config()


def test_rejects_a_warning_that_lands_after_deletion(monkeypatch):
    monkeypatch.setattr(accountmaint, "_warn_after", lambda: LIFETIME)

    with pytest.raises(accountmaint.ConfigError, match="unverified_account_warning"):
        accountmaint.check_config()


def test_accepts_the_shipped_defaults():
    accountmaint.check_config()
