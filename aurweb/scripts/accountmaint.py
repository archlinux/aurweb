#!/usr/bin/env python3
"""Warn, then delete, accounts that never verified and left nothing behind.

Distinct from usermaint, which only scrubs login IP addresses. This one
deletes rows, so it errs towards leaving an account alone: anything with a
package, comment, vote, request or notification survives regardless of age,
and so does any elevated account type.

Suspended accounts are *not* exempt from deletion. A suspension is not a claim
to the address, and an account with no content has nothing to preserve for an
audit trail. Note the consequence: deleting a suspended account frees its
username and address for re-registration. They are skipped by the warning pass
though -- there is no point inviting a banned account to come back.

Warnings are idempotent: the verification token minted when one is sent
doubles as the record that it went out, so an account is mailed at most once
per token TTL no matter how often this runs. Hourly is fine; so is daily.
"""

import argparse
import sys
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, or_

from aurweb import aur_logging, config, db, util
from aurweb.models import User
from aurweb.models.account_type import USER_ID
from aurweb.scripts import notify
from aurweb.users import verify
from aurweb.users.content import owns_content

logger = aur_logging.get_logger("aurweb.scripts.accountmaint")

# Deleting a user cascades into its dependents, so keep each statement small
# enough that a long-running first pass cannot sit on a huge lock set.
BATCH_SIZE = 500


def _warning_window() -> int:
    """Width of the warning band, which must exceed the gap between two runs.

    A band narrower than that gap drops a slice of accounts silently, and they
    are deleted on schedule without ever being warned.

    Duplicate mail is prevented by the live-token check in expiring(), not by
    keeping this tight, so the band can afford to be generous and a missed run
    is harmless. Matching the token's own TTL is what pins it to exactly one
    mail: an account warned on entering the band holds a live token for the
    whole time it stays inside. That is what makes any run interval shorter
    than this -- hourly, or every five minutes -- safe.
    """
    return verify.TTL


def _lifetime() -> int:
    return config.getint("options", "unverified_account_lifetime", fallback=1209600)


def _warn_after() -> int:
    return config.getint("options", "unverified_account_warning", fallback=604800)


def _doomed(now: datetime):
    """Accounts that will be deleted unless someone verifies them.

    Owning no content is not enough to call an account abandoned: someone who
    logs in or clones over ssh is using it whether or not they ever voted or
    commented. But "has ever authenticated" is the wrong test -- a bot logs in
    once on the way through registration, and treating that as a claim would
    exempt it permanently. The July 2026 waves did exactly this: 780 of those
    accounts carry a LastLogin from their signup day and nothing since.

    So the reprieve expires. An account has to have authenticated inside the
    same window it gets to stay unverified, which means a bot cannot buy
    immunity with one login -- it has to keep coming back, indefinitely, which
    is both expensive and conspicuous.
    """
    stale = int(now.timestamp()) - _lifetime()
    return db.query(User).filter(
        User.EmailVerified == 0,
        User.AccountTypeID == USER_ID,
        User.LastLogin < stale,
        User.LastSSHLogin < stale,
        ~owns_content(User.ID),
    )


def expiring(now: datetime) -> list[User]:
    """Accounts in the warning band that have not just been mailed.

    Suspended accounts are excluded: they are deleted without a warning.

    A live verification token is the record that a warning went out -- _warn()
    issues one for every account it mails, so "token still valid" means "warned
    within the last TTL". That makes this idempotent without a column of its
    own, and the run interval stops mattering.

    Reading a token as proof of a warning only holds because accounts reach
    this band long after registration: the token minted at signup has expired
    by then. It breaks if email_verification_ttl is ever raised above
    unverified_account_warning, which would leave signup tokens live into the
    band and silently warn nobody.
    """
    warn_after = _warn_after()
    return (
        _doomed(now)
        .filter(
            User.Suspended == 0,
            User.RegistrationTS < now - timedelta(seconds=warn_after),
            User.RegistrationTS
            >= now - timedelta(seconds=warn_after + _warning_window()),
            or_(
                User.EmailVerificationExpiry.is_(None),
                User.EmailVerificationExpiry <= int(now.timestamp()),
            ),
        )
        .all()
    )


def expired(now: datetime) -> list[int]:
    """IDs of accounts old enough to have verified, that never did."""
    query = _doomed(now).filter(
        User.RegistrationTS < now - timedelta(seconds=_lifetime())
    )
    return [user.ID for user in query.with_entities(User.ID)]


def _warn(now: datetime, dry_run: bool) -> int:
    users = expiring(now)
    if not users:
        return 0

    days_left = max(1, round((_lifetime() - _warn_after()) / 86400))
    if dry_run:
        logger.info("Would warn %d unverified accounts (dry run).", len(users))
        return len(users)

    # The registration token expired days ago, so each reminder needs a live
    # one. Commit before building notifications: they re-read the token.
    with db.begin():
        for user in users:
            verify.issue(user)

    notifs = [
        notify.VerificationReminderNotification(user.ID, days_left) for user in users
    ]
    util.apply_all(notifs, lambda n: n.send())

    logger.info("Warned %d unverified accounts.", len(users))
    return len(users)


def _delete(now: datetime, dry_run: bool) -> int:
    uids = expired(now)
    if not uids:
        return 0

    if dry_run:
        logger.info("Would delete %d unverified accounts (dry run).", len(uids))
        return len(uids)

    deleted = 0
    for offset in range(0, len(uids), BATCH_SIZE):
        batch = uids[offset : offset + BATCH_SIZE]
        with db.begin():
            result = db.get_session().execute(
                delete(User)
                .where(User.ID.in_(batch))
                .execution_options(synchronize_session=False)
            )
        deleted += result.rowcount
        logger.debug("Deleted %d/%d.", deleted, len(uids))

    logger.info("Deleted %d unverified accounts.", deleted)
    return deleted


class ConfigError(Exception):
    """The configured windows cannot produce correct behaviour."""


def check_config() -> None:
    """Refuse to run on a configuration whose failures would be silent.

    Every check here guards a mode where the script still exits 0, logs
    nothing unusual, and quietly does the wrong thing -- which is exactly the
    kind of breakage nobody notices until accounts are already gone.
    """
    lifetime, warn_after, ttl = _lifetime(), _warn_after(), _warning_window()

    if warn_after >= lifetime:
        raise ConfigError(
            f"unverified_account_warning ({warn_after}s) must be less than "
            f"unverified_account_lifetime ({lifetime}s), otherwise accounts "
            f"are deleted before -- or as -- they are warned."
        )

    if ttl >= warn_after:
        raise ConfigError(
            f"email_verification_ttl ({ttl}s) must be less than "
            f"unverified_account_warning ({warn_after}s). Warnings dedupe on "
            f"the verification token, and a TTL this long leaves the token "
            f"minted at signup still valid when the account reaches the "
            f"warning band, so nothing would ever be warned."
        )


def _main(dry_run: bool = False) -> tuple[int, int]:
    check_config()
    now = datetime.now(UTC)
    warned = _warn(now, dry_run)
    deleted = _delete(now, dry_run)
    if not (warned or deleted):
        logger.info("No unverified accounts to warn or delete.")
    return warned, deleted


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Warn and delete unverified accounts that left nothing behind."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="report what would happen, send no mail and delete nothing",
    )
    args = parser.parse_args()

    db.get_engine()
    try:
        _main(dry_run=args.dry_run)
    except ConfigError as exc:
        logger.error("Refusing to run: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    sys.exit(main())
