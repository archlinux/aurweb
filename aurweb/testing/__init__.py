from itertools import chain

import aurweb.db


def references_graph(table):
    """ Taken from Django's sqlite3/operations.py. """
    query = """
    WITH tables AS (
    SELECT :table name
    UNION
    SELECT sqlite_master.name
    FROM sqlite_master
    JOIN tables ON (sql REGEXP :regexp_1 || tables.name || :regexp_2)
    ) SELECT name FROM tables;
    """
    params = {
        "table": table,
        "regexp_1": r'(?i)\s+references\s+("|\')?',
        "regexp_2": r'("|\')?\s*\(',
    }
    cursor = aurweb.db.session.execute(query, params=params)
    return [row[0] for row in cursor.fetchall()]


def setup_test_db(*args):
    """ This function is to be used to setup a test database before
    using it. It takes a variable number of table strings, and for
    each table in that set of table strings, it deletes all records.

    The primary goal of this method is to configure empty tables
    that tests can use from scratch. This means that tests using
    this function should make sure they do not depend on external
    records and keep their logic self-contained.

    Generally used inside of pytest fixtures, this function
    can be used anywhere, but keep in mind its functionality when
    doing so.

    Examples:
        setup_test_db("Users", "Sessions")

        test_tables = ["Users", "Sessions"];
        setup_test_db(*test_tables)
    """
    # Make sure that we've grabbed the engine before using the session.
    aurweb.db.get_engine()

    tables = list(args)

    db_backend = aurweb.config.get("database", "backend")

    if db_backend != "sqlite":  # pragma: no cover
        aurweb.db.session.execute("SET FOREIGN_KEY_CHECKS = 0")
    else:
        # We're using sqlite, setup tables to be deleted without violating
        # foreign key constraints by graphing references.
        tables = set(chain.from_iterable(
            references_graph(table) for table in tables))

    for table in tables:
        aurweb.db.session.execute(f"DELETE FROM {table}")

    if db_backend != "sqlite":  # pragma: no cover
        aurweb.db.session.execute("SET FOREIGN_KEY_CHECKS = 1")

    # Expunge all objects from SQLAlchemy's IdentityMap.
    aurweb.db.session.expunge_all()
