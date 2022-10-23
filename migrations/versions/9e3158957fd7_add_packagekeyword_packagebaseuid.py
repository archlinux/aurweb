"""add PackageKeyword.PackageBaseUID index

Revision ID: 9e3158957fd7
Revises: 6441d3b65270
Create Date: 2022-10-17 11:11:46.203322

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "9e3158957fd7"
down_revision = "6441d3b65270"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(
        "KeywordsPackageBaseID", "PackageKeywords", ["PackageBaseID"], unique=False
    )


def downgrade():
    op.drop_index("KeywordsPackageBaseID", table_name="PackageKeywords")
