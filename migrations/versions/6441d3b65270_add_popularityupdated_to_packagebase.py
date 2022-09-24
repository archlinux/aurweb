"""add PopularityUpdated to PackageBase

Revision ID: 6441d3b65270
Revises: d64e5571bc8d
Create Date: 2022-09-22 18:08:03.280664

"""
from alembic import op
from sqlalchemy.exc import OperationalError

from aurweb.models.package_base import PackageBase
from aurweb.scripts import popupdate

# revision identifiers, used by Alembic.
revision = "6441d3b65270"
down_revision = "d64e5571bc8d"
branch_labels = None
depends_on = None

table = PackageBase.__table__


def upgrade():
    try:
        op.add_column(table.name, table.c.PopularityUpdated)
    except OperationalError:
        print(f"table '{table.name}' already exists, skipping migration")

    popupdate.run_variable()


def downgrade():
    op.drop_column(table.name, "PopularityUpdated")
