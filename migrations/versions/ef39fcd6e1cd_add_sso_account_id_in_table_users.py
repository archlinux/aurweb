"""Add SSO account ID in table Users

Revision ID: ef39fcd6e1cd
Revises: f47cad5d6d03
Create Date: 2020-06-08 10:04:13.898617

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision = "ef39fcd6e1cd"
down_revision = "f47cad5d6d03"
branch_labels = None
depends_on = None


def table_has_column(table, column_name):
    for element in Inspector.from_engine(op.get_bind()).get_columns(table):
        if element.get("name") == column_name:
            return True
    return False


def upgrade():
    if not table_has_column("Users", "SSOAccountID"):
        op.add_column(
            "Users", sa.Column("SSOAccountID", sa.String(length=255), nullable=True)
        )
        op.create_unique_constraint(None, "Users", ["SSOAccountID"])


def downgrade():
    if table_has_column("Users", "SSOAccountID"):
        op.drop_constraint("SSOAccountID", "Users", type_="unique")
        op.drop_column("Users", "SSOAccountID")
