"""Add HideDeletedComments to User

Revision ID: e4e49ffce091
Revises: 9e3158957fd7
Create Date: 2023-04-19 23:24:25.854874

"""
from alembic import op
from sqlalchemy.exc import OperationalError

from aurweb.models.user import User

# revision identifiers, used by Alembic.
revision = "e4e49ffce091"
down_revision = "9e3158957fd7"
branch_labels = None
depends_on = None

table = User.__table__


def upgrade():
    try:
        op.add_column(table.name, table.c.HideDeletedComments)
    except OperationalError:
        print(
            f"Column HideDeletedComments already exists in '{table.name}',"
            f" skipping migration."
        )


def downgrade():
    op.drop_column(table.name, "HideDeletedComments")
