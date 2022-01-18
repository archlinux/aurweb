"""utf8mb4 charset and collation

Revision ID: 56e2ce8e2ffa
Revises: ef39fcd6e1cd
Create Date: 2021-05-17 14:23:00.008479

"""
from alembic import op

import aurweb.config

# revision identifiers, used by Alembic.
revision = '56e2ce8e2ffa'
down_revision = 'ef39fcd6e1cd'
branch_labels = None
depends_on = None

# Tables affected by charset/collate change
tables = [
    ('AccountTypes', 'utf8mb4', 'utf8mb4_general_ci'),
    ('ApiRateLimit', 'utf8mb4', 'utf8mb4_general_ci'),
    ('Bans', 'utf8mb4', 'utf8mb4_general_ci'),
    ('DependencyTypes', 'utf8mb4', 'utf8mb4_general_ci'),
    ('Groups', 'utf8mb4', 'utf8mb4_general_ci'),
    ('Licenses', 'utf8mb4', 'utf8mb4_general_ci'),
    ('OfficialProviders', 'utf8mb4', 'utf8mb4_bin'),
    ('PackageBases', 'utf8mb4', 'utf8mb4_general_ci'),
    ('PackageBlacklist', 'utf8mb4', 'utf8mb4_general_ci'),
    ('PackageComments', 'utf8mb4', 'utf8mb4_general_ci'),
    ('PackageDepends', 'utf8mb4', 'utf8mb4_general_ci'),
    ('PackageKeywords', 'utf8mb4', 'utf8mb4_general_ci'),
    ('PackageRelations', 'utf8mb4', 'utf8mb4_general_ci'),
    ('PackageRequests', 'utf8mb4', 'utf8mb4_general_ci'),
    ('PackageSources', 'utf8mb4', 'utf8mb4_general_ci'),
    ('Packages', 'utf8mb4', 'utf8mb4_general_ci'),
    ('RelationTypes', 'utf8mb4', 'utf8mb4_general_ci'),
    ('RequestTypes', 'utf8mb4', 'utf8mb4_general_ci'),
    ('SSHPubKeys', 'utf8mb4', 'utf8mb4_bin'),
    ('Sessions', 'utf8mb4', 'utf8mb4_bin'),
    ('TU_VoteInfo', 'utf8mb4', 'utf8mb4_general_ci'),
    ('Terms', 'utf8mb4', 'utf8mb4_general_ci'),
    ('Users', 'utf8mb4', 'utf8mb4_general_ci')
]

# Indexes affected by charset/collate change
# Map of Unique Indexes key = index_name, value = [table_name, column1, column2]
indexes = {'ProviderNameProvides': ['OfficialProviders', 'Name', 'Provides']}

# Source charset/collation, before this migration is run.
src_charset = "utf8"
src_collate = "utf8_general_ci"

db_backend = aurweb.config.get("database", "backend")


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
    def op_execute(table_meta):
        table, charset, collate = table_meta
        sql = f"""
ALTER TABLE {table}
CONVERT TO CHARACTER SET {charset}
COLLATE {collate}
"""
        op.execute(sql)

    do_all(tables, op_execute)
    rebuild_unique_indexes_with_str_cols()


def downgrade():
    if db_backend == "sqlite":
        return None

    def op_execute(table_meta):
        table, charset, collate = table_meta
        sql = f"""
ALTER TABLE {table}
CONVERT TO CHARACTER SET {src_charset}
COLLATE {src_collate}
"""
        op.execute(sql)

    do_all(tables, op_execute)
    rebuild_unique_indexes_with_str_cols()
