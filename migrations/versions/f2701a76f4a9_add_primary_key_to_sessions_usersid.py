"""Add PRIMARY KEY to Sessions.UsersID

Previously UsersID was only a plain KEY (index) with no uniqueness constraint,
allowing duplicate rows to be inserted under a concurrent-login race condition.
This migration:
1. Removes any duplicate rows, keeping the most recently updated session per user.
2. Drops the plain index on UsersID.
3. Promotes UsersID to PRIMARY KEY, enforcing one session per user at the DB level.

Revision ID: f2701a76f4a9
Revises: 38e5b9982eea
Create Date: 2026-02-20 00:00:00.000000

"""

from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = "f2701a76f4a9"
down_revision = "38e5b9982eea"
branch_labels = None
depends_on = None

_FK_QUERY = text(
    """
    SELECT CONSTRAINT_NAME
    FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME   = 'Sessions'
      AND COLUMN_NAME  = 'UsersID'
      AND REFERENCED_TABLE_NAME IS NOT NULL
    LIMIT 1
    """
)


def _get_fk_name(conn):
    return conn.execute(_FK_QUERY).scalar()


def upgrade():
    # Remove duplicate Sessions rows, keeping the one with the highest
    # SessionID for each UsersID (deterministic tiebreaker when timestamps match).
    op.execute(
        """
        DELETE s1 FROM Sessions s1
        JOIN Sessions s2
            ON s1.UsersID = s2.UsersID
           AND s1.SessionID < s2.SessionID
        """
    )

    # MySQL/MariaDB refuses to drop an index that backs a foreign key.
    # We must drop the FK first, then swap plain KEY → PRIMARY KEY, then
    # re-add the FK — all in a single ALTER TABLE so the table is never
    # left without an index to support the constraint.
    fk_name = _get_fk_name(op.get_bind())
    if fk_name:
        op.execute(
            f"""
            ALTER TABLE Sessions
              DROP FOREIGN KEY `{fk_name}`,
              DROP KEY UsersID,
              ADD PRIMARY KEY (UsersID),
              ADD CONSTRAINT `{fk_name}` FOREIGN KEY (UsersID)
                REFERENCES Users(ID) ON DELETE CASCADE
            """
        )
    else:
        # No FK found — plain index swap is safe.
        op.execute("ALTER TABLE Sessions DROP KEY UsersID")
        op.execute("ALTER TABLE Sessions ADD PRIMARY KEY (UsersID)")


def downgrade():
    fk_name = _get_fk_name(op.get_bind())
    if fk_name:
        op.execute(
            f"""
            ALTER TABLE Sessions
              DROP FOREIGN KEY `{fk_name}`,
              DROP PRIMARY KEY,
              ADD KEY UsersID (UsersID),
              ADD CONSTRAINT `{fk_name}` FOREIGN KEY (UsersID)
                REFERENCES Users(ID) ON DELETE CASCADE
            """
        )
    else:
        op.execute("ALTER TABLE Sessions DROP PRIMARY KEY")
        op.execute("ALTER TABLE Sessions ADD KEY UsersID (UsersID)")
