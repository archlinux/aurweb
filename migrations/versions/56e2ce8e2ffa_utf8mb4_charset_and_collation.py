"""utf8mb4 charset and collation

Revision ID: 56e2ce8e2ffa
Revises: ef39fcd6e1cd
Create Date: 2021-05-17 14:23:00.008479

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '56e2ce8e2ffa'
down_revision = 'ef39fcd6e1cd'
branch_labels = None
depends_on = None

# Tables affected by charset/collate change
tables = ['AccountTypes', 'ApiRateLimit', 'Bans', 'DependencyTypes', 'Groups', 'Licenses', 'OfficialProviders',
          'PackageBases', 'PackageBlacklist', 'PackageComments', 'PackageDepends', 'PackageKeywords',
          'PackageRelations', 'PackageRequests', 'PackageSources', 'Packages', 'RelationTypes', 'RequestTypes',
          'SSHPubKeys', 'Sessions', 'TU_VoteInfo', 'Terms', 'Users']

# Indexes affected by charset/collate change
# Map of Unique Indexes key = index_name, value = [table_name, column1, column2]
indexes = {'ProviderNameProvides': ['OfficialProviders', 'Name', 'Provides']}

# Source charset/collation, before this migration is run.
src_charset = "utf8"
src_collate = "utf8_general_ci"

# Destination charset/collation, after this migration is run.
dst_charset = "utf8mb4"
dst_collate = "utf8mb4_bin"


def rebuild_unique_indexes_with_str_cols():
    for idx_name in indexes:
        sql = f"""
DROP INDEX IF EXISTS {idx_name} 
ON {indexes.get(idx_name)[0]}
"""
        op.execute(sql)
        sql = f"""
CREATE UNIQUE INDEX {idx_name} 
ON {indexes.get(idx_name)[0]} 
({indexes.get(idx_name)[1]}, {indexes.get(idx_name)[2]}) 
"""
        op.execute(sql)


def do_all(iterable, fn):
    for element in iterable:
        fn(element)


def upgrade():
    def op_execute(table):
        sql = f"""
ALTER TABLE {table} 
CONVERT TO CHARACTER SET {dst_charset} 
COLLATE {dst_collate}
"""
        op.execute(sql)

    do_all(tables, op_execute)
    rebuild_unique_indexes_with_str_cols()


def downgrade():
    def op_execute(table):
        sql = f"""
ALTER TABLE {table} 
CONVERT TO CHARACTER SET {src_charset} 
COLLATE {src_collate}
"""
        op.execute(sql)

    do_all(tables, op_execute)
    rebuild_unique_indexes_with_str_cols()
