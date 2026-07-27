"""Add NormalizedEmail to User

Revision ID: b7c419f0a2d1
Revises: b7e4a1c9f0d2
Create Date: 2026-07-26 00:00:00.000000

The backfill has to read rows, so `alembic upgrade --sql` cannot render this.
"""

import sqlalchemy as sa
from alembic import op

from aurweb.models.user import User
from aurweb.util import normalize_email

# revision identifiers, used by Alembic.
revision = "b7c419f0a2d1"
down_revision = "b7e4a1c9f0d2"
branch_labels = None
depends_on = None

table = User.__table__
column = "NormalizedEmail"
index = "UsersNormalizedEmail"


# Sessions and AcceptedTerms are left out because a bot registration gets both
# for free. VoteInfo and Votes are in because deleting a submitter cascades the
# whole proposal and every vote cast on it.
content_columns = {
    "PackageComments": ["UsersID", "EditedUsersID", "DelUsersID"],
    "PackageBases": ["MaintainerUID", "SubmitterUID", "PackagerUID", "FlaggerUID"],
    "PackageVotes": ["UsersID"],
    "PackageComaintainers": ["UsersID"],
    "PackageRequests": ["UsersID", "ClosedUID"],
    "PackageNotifications": ["UserID"],
    "SSHPubKeys": ["UserID"],
    "VoteInfo": ["SubmitterID"],
    "Votes": ["UserID"],
}


def _has_content(uid: str) -> str:
    """One EXISTS per column rather than `uid IN (col, col)`. MariaDB cannot
    use an index for the IN form inside a correlated subquery, so it scans
    the whole table for every candidate row.
    """
    return "(%s)" % " OR ".join(
        f"EXISTS (SELECT 1 FROM `{name}` WHERE `{col}` = {uid})"
        for name, columns in content_columns.items()
        for col in columns
    )


def _backfill(conn) -> None:
    # Recompute all rows; an aborted run may have committed partial state.
    rows = conn.execute(sa.text(f"SELECT `ID`, `Email` FROM `{table.name}`")).fetchall()
    if not rows:
        return

    conn.execute(
        sa.text(f"UPDATE `{table.name}` SET `{column}` = :normalized WHERE `ID` = :id"),
        [{"id": uid, "normalized": normalize_email(email)} for uid, email in rows],
    )
    print(f"Wrote {len(rows)} '{table.name}'.{column} values.")


def _null_duplicates(conn) -> None:
    # The index compares by collation, Python by codepoint; group in SQL,
    # key on GroupID.
    rows = conn.execute(
        sa.text(
            f"SELECT dupes.`GroupID`, u.`{column}`, u.`ID`, u.`Username`, u.`Email`, "
            f"u.`Suspended`, u.`EmailVerified`, "
            f"{_has_content('u.`ID`')} AS `HasContent` "
            f"FROM `{table.name}` u JOIN "
            f"(SELECT `{column}` AS `Address`, MIN(`ID`) AS `GroupID` "
            f"FROM `{table.name}` GROUP BY `{column}` HAVING COUNT(*) > 1) AS dupes "
            f"ON u.`{column}` = dupes.`Address` "
            f"ORDER BY dupes.`GroupID`, u.`ID`"
        )
    ).fetchall()
    if not rows:
        return

    groups: dict = {}
    for row in rows:
        groups.setdefault(row.GroupID, []).append(row)

    print()
    print(f"{len(groups)} canonical addresses have more than one account.")
    print(f"Clearing {column} on every member except the group's primary, if")
    print("it has one. NULL is exempt from the unique index. This step deletes")
    print("no account and changes no other column.")

    demoted = []
    for members in groups.values():
        # No member verified their address or left content, so none of them
        # has a claim to it.
        keeper_id = None
        if any(m.EmailVerified or m.HasContent for m in members):
            keeper_id = min(
                members,
                key=lambda m: (
                    m.Suspended,
                    not (m.EmailVerified or m.HasContent),
                    # user@gmail.com outranks user+tag@gmail.com.
                    m.Email.lower() != m.NormalizedEmail.lower(),
                    m.ID,
                ),
            ).ID
        print()
        print(f"  {members[0].NormalizedEmail}")
        for member in members:
            mark = "keep" if member.ID == keeper_id else "null"
            print(
                f"    [{mark}] ID={member.ID} "
                f"Username={member.Username} Email={member.Email}"
            )
            if member.ID != keeper_id:
                demoted.append(member.ID)

    conn.execute(
        sa.text(f"UPDATE `{table.name}` SET `{column}` = NULL WHERE `ID` = :id"),
        [{"id": uid} for uid in demoted],
    )
    print()
    print(f"Cleared {column} on {len(demoted)} duplicate accounts.")


def _ensure_dynamic_row_format(conn) -> None:
    # The 1280-byte key needs DYNAMIC row format; COMPACT caps keys at 767.
    if conn.dialect.name != "mysql":
        return
    fmt = conn.execute(
        sa.text(
            "SELECT ROW_FORMAT FROM information_schema.TABLES "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = :name"
        ),
        {"name": table.name},
    ).scalar()
    if fmt not in ("Dynamic", "Compressed"):
        print(f"Rebuilding '{table.name}' as ROW_FORMAT=DYNAMIC (was {fmt}).")
        op.execute(f"ALTER TABLE `{table.name}` ROW_FORMAT=DYNAMIC")


def upgrade():
    conn = op.get_bind()

    if column not in [c["name"] for c in sa.inspect(conn).get_columns(table.name)]:
        op.add_column(table.name, sa.Column(column, sa.String(320), nullable=True))
    else:
        print(f"Column {column} already exists in '{table.name}', skipping.")

    _backfill(conn)
    _null_duplicates(conn)

    _ensure_dynamic_row_format(conn)
    op.create_index(index, table.name, [column], unique=True)


def downgrade():
    # Index first; sqlite refuses to drop a column an index references.
    op.drop_index(index, table_name=table.name)
    op.drop_column(table.name, column)
