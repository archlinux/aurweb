"""Whether a user left anything behind that outlives the account.

Sessions, AcceptedTerms and SSHPubKeys are deliberately absent: registration
takes all three in one POST, before any verification, so they say nothing
about a real user. VoteInfo and Votes are present because deleting a
submitter cascades the whole proposal and every vote cast on it.
"""

from sqlalchemy import exists, or_
from sqlalchemy.sql.elements import ColumnElement

from aurweb import models

CONTENT_COLUMNS: tuple[tuple[type, tuple[str, ...]], ...] = (
    (models.PackageComment, ("UsersID", "EditedUsersID", "DelUsersID")),
    (
        models.PackageBase,
        ("MaintainerUID", "SubmitterUID", "PackagerUID", "FlaggerUID"),
    ),
    (models.PackageVote, ("UsersID",)),
    (models.PackageComaintainer, ("UsersID",)),
    (models.PackageRequest, ("UsersID", "ClosedUID")),
    (models.PackageNotification, ("UserID",)),
    (models.VoteInfo, ("SubmitterID",)),
    (models.Vote, ("UserID",)),
)


def owns_content(user_id: ColumnElement) -> ColumnElement:
    """A predicate that is true when `user_id` appears in any content table.

    One EXISTS per column rather than `user_id IN (col, col)`. MariaDB cannot
    use an index for the IN form inside a correlated subquery, so it scans the
    whole table for every candidate row.
    """
    return or_(
        *[
            exists().where(getattr(model, column) == user_id)
            for model, columns in CONTENT_COLUMNS
            for column in columns
        ]
    )
