"""Run the alembic migrations against a real database.

The rest of the suite gets its schema from metadata.create_all plus an
`alembic stamp head` (aurweb.initdb), so migration code is never executed
anywhere else. These tests walk the revision chain down to FLOOR and back,
then verify the migrated schema matches aurweb.schema.
"""

import pathlib

import alembic.command
import alembic.config
import pytest
import sqlalchemy as sa

import aurweb.db
import aurweb.schema

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

# Migrations below the floor assume production-shaped data.
FLOOR = "f2701a76f4a9"


@pytest.fixture(autouse=True)
def setup(db_test):
    return


def alembic_config() -> alembic.config.Config:
    config = alembic.config.Config(str(REPO_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(REPO_ROOT / "migrations"))
    config.attributes["configure_logger"] = False
    return config


def test_downgrade_upgrade_roundtrip():
    config = alembic_config()
    # Twice: cycle two runs against a migration-built schema, not create_all's.
    for _ in range(2):
        alembic.command.downgrade(config, FLOOR)
        alembic.command.upgrade(config, "head")


def _unique_constraints(table: sa.Table) -> set[tuple[tuple[str, ...], bool]]:
    """Column(unique=True) constraints. Their index names are picked by the
    dialect, so they can only be matched by column tuple."""
    return {
        (tuple(col.name for col in constraint.columns), True)
        for constraint in table.constraints
        if isinstance(constraint, sa.UniqueConstraint)
    }


def _backs_foreign_key(columns: tuple[str, ...], table: sa.Table) -> bool:
    """InnoDB silently creates and drops an index on exactly an FK's
    constrained columns. Its name and existence are not ours to assert on."""
    return any(
        columns == tuple(col.name for col in fk.columns)
        for fk in table.foreign_key_constraints
    )


def test_migrated_schema_matches_metadata():
    config = alembic_config()
    alembic.command.downgrade(config, FLOOR)
    alembic.command.upgrade(config, "head")

    inspector = sa.inspect(aurweb.db.get_engine())
    metadata = aurweb.schema.metadata

    tables = set(inspector.get_table_names())
    assert tables - set(metadata.tables) == {"alembic_version"}
    assert set(metadata.tables) <= tables

    for name, table in metadata.tables.items():
        db_columns = {col["name"]: col for col in inspector.get_columns(name)}
        assert set(db_columns) == {col.name for col in table.columns}, name
        for col in table.columns:
            # MySQL forces PK columns NOT NULL regardless of the declaration.
            expected = col.nullable and not col.primary_key
            assert db_columns[col.name]["nullable"] == expected, (
                f"{name}.{col.name} nullable"
            )

        db_indexes = {
            index["name"]: (tuple(index["column_names"]), bool(index["unique"]))
            for index in inspector.get_indexes(name)
        }
        declared_names = {index.name for index in table.indexes}
        for index in table.indexes:
            assert db_indexes.get(index.name) == (
                tuple(col.name for col in index.columns),
                bool(index.unique),
            ), f"{name}.{index.name}"
        uniques = _unique_constraints(table)
        missing = uniques - set(db_indexes.values())
        assert not missing, f"{name}: missing unique indexes {missing}"
        for index_name, (columns, unique) in db_indexes.items():
            if index_name in declared_names:
                continue
            assert (columns, unique) in uniques or _backs_foreign_key(columns, table), (
                f"{name}.{index_name} exists in the database but is not "
                f"declared in aurweb.schema"
            )

        db_fks = {
            (
                tuple(fk["constrained_columns"]),
                fk["referred_table"],
                tuple(fk["referred_columns"]),
            )
            for fk in inspector.get_foreign_keys(name)
        }
        for fk in table.foreign_key_constraints:
            key = (
                tuple(col.name for col in fk.columns),
                fk.referred_table.name,
                tuple(element.column.name for element in fk.elements),
            )
            assert key in db_fks, f"{name}: missing foreign key {key}"
