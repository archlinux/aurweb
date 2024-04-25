"""Rename TU tables/columns

Revision ID: 7d65d35fae45
Revises: 6a64dd126029
Create Date: 2023-09-10 10:21:33.092342

"""

from alembic import op
from sqlalchemy.dialects.mysql import INTEGER

# revision identifiers, used by Alembic.
revision = "7d65d35fae45"
down_revision = "6a64dd126029"
branch_labels = None
depends_on = None

# TU_VoteInfo -> VoteInfo
# TU_VoteInfo.ActiveTUs -> VoteInfo.ActiveUsers
# TU_Votes -> Votes


def upgrade():
    # Tables
    op.rename_table("TU_VoteInfo", "VoteInfo")
    op.rename_table("TU_Votes", "Votes")

    # Columns
    op.alter_column(
        "VoteInfo",
        "ActiveTUs",
        existing_type=INTEGER(unsigned=True),
        new_column_name="ActiveUsers",
    )


def downgrade():
    # Tables
    op.rename_table("VoteInfo", "TU_VoteInfo")
    op.rename_table("Votes", "TU_Votes")

    # Columns
    op.alter_column(
        "TU_VoteInfo",
        "ActiveUsers",
        existing_type=INTEGER(unsigned=True),
        new_column_name="ActiveTUs",
    )
