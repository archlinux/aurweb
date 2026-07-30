"""add adoption request type

Revision ID: b7e4a1c9f0d2
Revises: a3f1c2d4e5b6
Create Date: 2026-07-29 20:35:00.000000

"""

from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = "b7e4a1c9f0d2"
down_revision = "a3f1c2d4e5b6"
branch_labels = None
depends_on = None


def upgrade():
    connection = op.get_bind()
    connection.execute(
        text(
            "INSERT INTO RequestTypes (ID, Name) VALUES (4, 'adoption') "
            "ON DUPLICATE KEY UPDATE Name = Name"
        )
    )


def downgrade():
    op.execute("DELETE FROM RequestTypes WHERE ID = 4")
