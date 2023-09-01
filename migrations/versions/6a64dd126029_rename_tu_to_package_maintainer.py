"""Rename TU to Package Maintainer

Revision ID: 6a64dd126029
Revises: c5a6a9b661a0
Create Date: 2023-09-01 13:48:15.315244

"""
from aurweb import db
from aurweb.models import AccountType

# revision identifiers, used by Alembic.
revision = "6a64dd126029"
down_revision = "c5a6a9b661a0"
branch_labels = None
depends_on = None

# AccountTypes
# ID 2 -> Trusted User / Package Maintainer
# ID 4 -> Trusted User & Developer / Package Maintainer & Developer


def upgrade():
    with db.begin():
        tu = db.query(AccountType).filter(AccountType.ID == 2).first()
        tudev = db.query(AccountType).filter(AccountType.ID == 4).first()

        tu.AccountType = "Package Maintainer"
        tudev.AccountType = "Package Maintainer & Developer"


def downgrade():
    with db.begin():
        pm = db.query(AccountType).filter(AccountType.ID == 2).first()
        pmdev = db.query(AccountType).filter(AccountType.ID == 4).first()

        pm.AccountType = "Trusted User"
        pmdev.AccountType = "Trusted User & Developer"
