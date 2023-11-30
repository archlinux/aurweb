import argparse

import alembic.command
import alembic.config

import aurweb.aur_logging
import aurweb.db
import aurweb.schema


def feed_initial_data(conn):
    conn.execute(
        aurweb.schema.AccountTypes.insert(),
        [
            {"AccountType": "User"},
            {"AccountType": "Package Maintainer"},
            {"AccountType": "Developer"},
            {"AccountType": "Package Maintainer & Developer"},
        ],
    )
    conn.execute(
        aurweb.schema.DependencyTypes.insert(),
        [
            {"Name": "depends"},
            {"Name": "makedepends"},
            {"Name": "checkdepends"},
            {"Name": "optdepends"},
        ],
    )
    conn.execute(
        aurweb.schema.RelationTypes.insert(),
        [
            {"Name": "conflicts"},
            {"Name": "provides"},
            {"Name": "replaces"},
        ],
    )
    conn.execute(
        aurweb.schema.RequestTypes.insert(),
        [
            {"Name": "deletion"},
            {"Name": "orphan"},
            {"Name": "merge"},
        ],
    )


def run(args):
    aurweb.config.rehash()

    # Ensure Alembic is fine before we do the real work, in order not to fail at
    # the last step and leave the database in an inconsistent state. The
    # configuration is loaded lazily, so we query it to force its loading.
    if args.use_alembic:
        alembic_config = alembic.config.Config("alembic.ini")
        alembic_config.get_main_option("script_location")
        alembic_config.attributes["configure_logger"] = False

    engine = aurweb.db.get_engine(echo=(args.verbose >= 1))
    conn = engine.connect()
    # conn.execute("CREATE COLLATION ci (provider = icu, locale = 'und-u-ks-level2', deterministic = false)")  # noqa: E501
    aurweb.schema.metadata.create_all(engine)
    with conn.begin():
        feed_initial_data(conn)
    conn.close()

    if args.use_alembic:
        alembic.command.stamp(alembic_config, "head")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="python -m aurweb.initdb", description="Initialize the aurweb database."
    )
    parser.add_argument(
        "-v", "--verbose", action="count", default=0, help="increase verbosity"
    )
    parser.add_argument(
        "--no-alembic",
        help="disable Alembic migrations support",
        dest="use_alembic",
        action="store_false",
    )
    args = parser.parse_args()
    run(args)
