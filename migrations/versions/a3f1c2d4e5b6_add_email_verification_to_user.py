"""Add email verification to User

Revision ID: a3f1c2d4e5b6
Revises: f2701a76f4a9
Create Date: 2026-06-13 00:00:00.000000

"""

from alembic import op
from sqlalchemy.exc import OperationalError

from aurweb.models.user import User

# revision identifiers, used by Alembic.
revision = "a3f1c2d4e5b6"
down_revision = "f2701a76f4a9"
branch_labels = None
depends_on = None

table = User.__table__


def upgrade():
    for column in (
        "EmailVerified",
        "EmailVerificationToken",
        "EmailVerificationExpiry",
    ):
        try:
            op.add_column(table.name, table.c[column])
        except OperationalError:
            print(f"Column {column} already exists in '{table.name}', skipping.")

    # Grandfather existing accounts that completed registration (set a password)
    op.execute("UPDATE `Users` SET `EmailVerified` = 1 WHERE `Passwd` <> ''")


def downgrade():
    op.drop_column(table.name, "EmailVerificationExpiry")
    op.drop_column(table.name, "EmailVerificationToken")
    op.drop_column(table.name, "EmailVerified")
