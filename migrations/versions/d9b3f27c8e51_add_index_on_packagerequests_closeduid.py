"""Add index on PackageRequests.ClosedUID

Revision ID: d9b3f27c8e51
Revises: b7c419f0a2d1
Create Date: 2026-08-05 21:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "d9b3f27c8e51"
down_revision = "b7c419f0a2d1"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index("RequestsClosedUID", "PackageRequests", ["ClosedUID"])


def downgrade():
    # InnoDB backs the ClosedUID FK with this index, so the FK must go first.
    conn = op.get_bind()
    if conn.dialect.name != "mysql":
        op.drop_index("RequestsClosedUID", table_name="PackageRequests")
        return

    fks = [
        fk
        for fk in sa.inspect(conn).get_foreign_keys("PackageRequests")
        if fk["constrained_columns"] == ["ClosedUID"]
    ]
    for fk in fks:
        op.drop_constraint(fk["name"], "PackageRequests", type_="foreignkey")
    op.drop_index("RequestsClosedUID", table_name="PackageRequests")
    for fk in fks:
        op.create_foreign_key(
            fk["name"],
            "PackageRequests",
            "Users",
            ["ClosedUID"],
            ["ID"],
            ondelete=fk["options"].get("ondelete"),
        )
