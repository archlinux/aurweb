"""add SSHPubKeys.PubKey index

Revision ID: dd70103d2e82
Revises: d64e5571bc8d
Create Date: 2022-08-12 21:30:26.155465

"""
import traceback

from alembic import op

# revision identifiers, used by Alembic.
revision = 'dd70103d2e82'
down_revision = 'd64e5571bc8d'
branch_labels = None
depends_on = None


def upgrade():
    try:
        op.create_index("SSHPubKeysPubKey", "SSHPubKeys", ["PubKey"])
    except Exception:
        traceback.print_exc()
        print("failing silently...")


def downgrade():
    op.drop_index("SSHPubKeysPubKey", "SSHPubKeys")
