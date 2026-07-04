"""add flagged-malicious columns to PackageBase

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-06-24 00:00:01.000000

"""

from alembic import op
from sqlalchemy.exc import OperationalError

from aurweb.models.package_base import PackageBase

# revision identifiers, used by Alembic.
revision = "b2c3d4e5f6a7"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None

table = PackageBase.__table__

COLUMNS = ("FlaggedMaliciousTS", "FlaggedMaliciousUID", "FlaggedMaliciousComment")


def upgrade():
    for name in COLUMNS:
        try:
            op.add_column(table.name, table.c[name])
        except OperationalError:
            print(f"column '{name}' already exists, skipping")


def downgrade():
    for name in reversed(COLUMNS):
        op.drop_column(table.name, name)
