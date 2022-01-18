"""
upgrade voteinfo integers

Within `aurweb/schema.py`, these were previously forced to use
TINYINT(3, unsigned=True) types. When generating with dummy data,
it is very easy to bypass 3-character TU counts; in addition,
this is possible in the future on production, and so we should
deal with this case regardless.

All previous TINYINT(3, unsigned=True) typed columns are upgraded
INTEGER(unsigned=True) types, supporting up to 4-bytes of active TUs
and votes for one particular proposal.

Revision ID: be7adae47ac3
Revises: 56e2ce8e2ffa
Create Date: 2022-01-06 14:37:07.899778
"""
from alembic import op
from sqlalchemy.dialects.mysql import INTEGER, TINYINT

# revision identifiers, used by Alembic.
revision = 'be7adae47ac3'
down_revision = '56e2ce8e2ffa'
branch_labels = None
depends_on = None

# Upgrade to INTEGER(unsigned=True); supports 4-byte values.
UPGRADE_T = INTEGER(unsigned=True)

# Downgrade to TINYINT(3, unsigned=True); supports 1-byte values.
DOWNGRADE_T = TINYINT(3, unsigned=True)


def upgrade():
    """ Upgrade 'Yes', 'No', 'Abstain' and 'ActiveTUs' to unsigned INTEGER. """
    op.alter_column("TU_VoteInfo", "Yes", type_=UPGRADE_T)
    op.alter_column("TU_VoteInfo", "No", type_=UPGRADE_T)
    op.alter_column("TU_VoteInfo", "Abstain", type_=UPGRADE_T)
    op.alter_column("TU_VoteInfo", "ActiveTUs", type_=UPGRADE_T)


def downgrade():
    """
    Downgrade 'Yes', 'No', 'Abstain' and 'ActiveTUs' to unsigned TINYINT.
    """
    op.alter_column("TU_VoteInfo", "ActiveTUs", type_=DOWNGRADE_T)
    op.alter_column("TU_VoteInfo", "Abstain", type_=DOWNGRADE_T)
    op.alter_column("TU_VoteInfo", "No", type_=DOWNGRADE_T)
    op.alter_column("TU_VoteInfo", "Yes", type_=DOWNGRADE_T)
