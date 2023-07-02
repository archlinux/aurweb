"""Add index on PackageBases.Popularity and .Name

Revision ID: c5a6a9b661a0
Revises: e4e49ffce091
Create Date: 2023-07-02 13:46:52.522146

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "c5a6a9b661a0"
down_revision = "e4e49ffce091"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(
        "BasesPopularityName", "PackageBases", ["Popularity", "Name"], unique=False
    )


def downgrade():
    op.drop_index("BasesPopularityName", table_name="PackageBases")
