"""Add index on PackageRequests.ClosedUID

Revision ID: d9b3f27c8e51
Revises: b7c419f0a2d1
Create Date: 2026-08-05 21:00:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "d9b3f27c8e51"
down_revision = "b7c419f0a2d1"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index("RequestsClosedUID", "PackageRequests", ["ClosedUID"])


def downgrade():
    op.drop_index("RequestsClosedUID", table_name="PackageRequests")
