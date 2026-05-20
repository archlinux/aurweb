"""Add surrogate ID primary key to PackageRelations

The ORM had a composite PK including RelTypeID, which callers mutate.
Mutating a PK column breaks identity-map tracking. Add a real surrogate ID.

Revision ID: a7c14de0a8e2
Revises: f2701a76f4a9
Create Date: 2026-05-19 21:00:00.000000

"""

from alembic import op

revision = "a7c14de0a8e2"
down_revision = "f2701a76f4a9"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        ALTER TABLE PackageRelations
          ADD COLUMN ID INT(10) UNSIGNED NOT NULL AUTO_INCREMENT FIRST,
          ADD PRIMARY KEY (ID)
        """
    )


def downgrade():
    op.execute(
        """
        ALTER TABLE PackageRelations
          DROP PRIMARY KEY,
          DROP COLUMN ID
        """
    )
