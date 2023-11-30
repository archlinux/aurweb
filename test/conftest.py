"""
pytest configuration.

The conftest.py file is used to define pytest-global fixtures
or actions run before tests.

Module scoped fixtures:
----------------------
- setup_database
- db_session (depends: setup_database)

Function scoped fixtures:
------------------------
- db_test (depends: db_session)

Tests in aurweb which access the database **must** use the `db_test`
function fixture. Most database tests simply require this fixture in
an autouse=True setup fixture, or for fixtures used in DB tests example:

    # In scenarios which there are no other database fixtures
    # or other database fixtures dependency paths don't always
    # hit `db_test`.
    @pytest.fixture(autouse=True)
    def setup(db_test):
        return

    # In scenarios where we can embed the `db_test` fixture in
    # specific fixtures that already exist.
    @pytest.fixture
    def user(db_test):
        with db.begin():
            user = db.create(User, ...)
        yield user

The `db_test` fixture triggers our module-level database fixtures,
then clears the database for each test function run in that module.
It is done this way because migration has a large cost; migrating
ahead of each function takes too long when compared to this method.
"""
import os
import pathlib
from multiprocessing import Lock

import py
import pytest
from prometheus_client import values
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from sqlalchemy.engine.base import Engine
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.orm import scoped_session

import aurweb.config
import aurweb.db
import aurweb.schema
from aurweb import aur_logging, initdb, testing
from aurweb.testing.email import Email
from aurweb.testing.git import GitRepository
from aurweb.testing.prometheus import clear_metrics

logger = aur_logging.get_logger(__name__)

# Synchronization lock for database setup.
setup_lock = Lock()

# Disable prometheus multiprocess mode for tests
values.ValueClass = values.MutexValue


def test_engine() -> Engine:
    """
    Return a privileged SQLAlchemy engine with default database.

    This method is particularly useful for providing an engine that
    can be used to create and drop databases from an SQL server.

    :return: SQLAlchemy Engine instance (connected to a default)
    """
    socket = aurweb.config.get_with_fallback("database", "socket", None)
    host = aurweb.config.get_with_fallback("database", "host", None)
    port = aurweb.config.get_with_fallback("database", "port", None)

    kwargs = {
        "database": aurweb.config.get("database", "name"),
        "username": aurweb.config.get("database", "user"),
        "password": aurweb.config.get_with_fallback("database", "password", None),
        "host": socket if socket else host,
        "port": port if not socket else None,
    }

    backend = aurweb.config.get("database", "backend")
    driver = aurweb.db.DRIVERS.get(backend)
    return create_engine(URL.create(driver, **kwargs), isolation_level="AUTOCOMMIT")


class AlembicArgs:
    """
    Masquerade an ArgumentParser like structure.

    This structure is needed to pass conftest-specific arguments
    to initdb.run duration database creation.
    """

    verbose = False
    use_alembic = True


def _create_database(engine: Engine, dbname: str) -> None:
    """
    Create a test database.

    :param engine: Engine returned by test_engine()
    :param dbname: Database name to create
    """
    conn = engine.connect()
    with conn.begin():
        try:
            conn.execute(text(f"CREATE DATABASE {dbname}"))
        except ProgrammingError:  # pragma: no cover
            # The database most likely already existed if we hit
            # a ProgrammingError. Just drop the database and try
            # again. If at that point things still fail, any
            # exception will be propogated up to the caller.
            conn.execute(text(f"DROP DATABASE {dbname} WITH (FORCE)"))
            conn.execute(text(f"CREATE DATABASE {dbname}"))
    conn.close()
    initdb.run(AlembicArgs)


def _drop_database(engine: Engine, dbname: str) -> None:
    """
    Drop a test database.

    :param engine: Engine returned by test_engine()
    :param dbname: Database name to drop
    """
    aurweb.schema.metadata.drop_all(bind=engine)
    conn = engine.connect()
    conn.execute(text(f"DROP DATABASE {dbname}"))
    conn.close()


def setup_email():
    if not os.path.exists(Email.TEST_DIR):
        # Create the directory.
        os.makedirs(Email.TEST_DIR, exist_ok=True)

    # Cleanup all email files for this test suite.
    prefix = Email.email_prefix(suite=True)
    files = os.listdir(Email.TEST_DIR)
    for file in files:
        if file.startswith(prefix):
            os.remove(os.path.join(Email.TEST_DIR, file))


@pytest.fixture(scope="module")
def setup_database(tmp_path_factory: pathlib.Path, worker_id: str) -> None:
    """Create and drop a database for the suite this fixture is used in."""
    engine = test_engine()
    dbname = aurweb.db.name()

    setup_email()
    _create_database(engine, dbname)
    yield  # Run the test function depending on this fixture.
    _drop_database(engine, dbname)  # Cleanup the database.


@pytest.fixture(scope="module")
def db_session(setup_database: None) -> scoped_session:
    """
    Yield a database session based on aurweb.db.name().

    The returned session is popped out of persistence after the test is run.
    """
    # After the test runs, aurweb.db.name() ends up returning the
    # configured database, because PYTEST_CURRENT_TEST is removed.
    dbname = aurweb.db.name()
    session = aurweb.db.get_session()

    yield session

    # Close the session and pop it.
    session.close()
    aurweb.db.pop_session(dbname)

    # Dispose engine and close connections
    aurweb.db.get_engine(dbname).dispose()
    aurweb.db.pop_engine(dbname)


@pytest.fixture
def db_test(db_session: scoped_session) -> None:
    """
    Database test fixture.

    This fixture should be included in any tests which access the
    database. It ensures that a test database is created and
    alembic migrated, takes care of dropping the database when
    the module is complete, and runs setup_test_db() to clear out
    tables for each test.

    Tests using this fixture should access the database
    session via aurweb.db.get_session().
    """
    testing.setup_test_db()


@pytest.fixture
def git(tmpdir: py.path.local) -> GitRepository:
    yield GitRepository(tmpdir)


@pytest.fixture
def email_test() -> None:
    """
    A decoupled test email setup fixture.

    When using the `db_test` fixture, this fixture is redundant. Otherwise,
    email tests need to run through our `setup_email` function to ensure
    that we set them up to be used via aurweb.testing.email.Email.
    """
    setup_email()


@pytest.fixture
def prometheus_test():
    """
    Prometheus test fixture

    Removes any existing values from our metrics
    """
    clear_metrics()
