"""fix pkgvote votets

Revision ID: d64e5571bc8d
Revises: be7adae47ac3
Create Date: 2022-02-18 12:47:05.322766

"""
from datetime import datetime

import sqlalchemy as sa

from alembic import op

from aurweb import db
from aurweb.models import PackageVote

# revision identifiers, used by Alembic.
revision = 'd64e5571bc8d'
down_revision = 'be7adae47ac3'
branch_labels = None
depends_on = None

table = PackageVote.__tablename__
column = 'VoteTS'
epoch = datetime(1970, 1, 1)


def upgrade():
    with db.begin():
        records = db.query(PackageVote).filter(PackageVote.VoteTS.is_(None))
        for record in records:
            record.VoteTS = epoch.timestamp()
    op.alter_column(table, column, existing_type=sa.BIGINT(), nullable=False)


def downgrade():
    op.alter_column(table, column, existing_type=sa.BIGINT(), nullable=True)
