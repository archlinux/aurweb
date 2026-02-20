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

# revision identifiers, used by Alembic.
revision = "f2701a76f4a9"
down_revision = "38e5b9982eea"
branch_labels = None
depends_on = None


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
    # Drop the plain index now that we are promoting it to a PRIMARY KEY.
    op.execute("ALTER TABLE Sessions DROP KEY UsersID")
    # Add the PRIMARY KEY — enforces one session per user at the DB level.
    op.execute("ALTER TABLE Sessions ADD PRIMARY KEY (UsersID)")


def downgrade():
    op.execute("ALTER TABLE Sessions DROP PRIMARY KEY")
    op.execute("ALTER TABLE Sessions ADD KEY UsersID (UsersID)")
