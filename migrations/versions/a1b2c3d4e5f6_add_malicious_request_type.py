"""add malicious request type

Revision ID: a1b2c3d4e5f6
Revises: f2701a76f4a9
Create Date: 2026-06-24 00:00:00.000000

"""

from alembic import op
from sqlalchemy import column, table
from sqlalchemy.sql import select

# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "f2701a76f4a9"
branch_labels = None
depends_on = None

MALICIOUS_ID = 4

RequestTypes = table("RequestTypes", column("ID"), column("Name"))


def upgrade():
    conn = op.get_bind()
    exists = conn.execute(
        select(RequestTypes.c.ID).where(RequestTypes.c.ID == MALICIOUS_ID)
    ).first()
    if not exists:
        op.bulk_insert(RequestTypes, [{"ID": MALICIOUS_ID, "Name": "malicious"}])


def downgrade():
    conn = op.get_bind()
    conn.execute(RequestTypes.delete().where(RequestTypes.c.ID == MALICIOUS_ID))
