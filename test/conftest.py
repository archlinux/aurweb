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
from posix_ipc import O_CREAT, Semaphore
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.engine.base import Engine
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.orm import scoped_session

import aurweb.config
import aurweb.db
from aurweb import aur_logging, initdb, testing
from aurweb.testing.email import Email
from aurweb.testing.filelock import FileLock
from aurweb.testing.git import GitRepository

logger = aur_logging.get_logger(__name__)

# Synchronization lock for database setup.
setup_lock = Lock()


def test_engine() -> Engine:
    """
    Return a privileged SQLAlchemy engine with no database.

    This method is particularly useful for providing an engine that
    can be used to create and drop databases from an SQL server.

    :return: SQLAlchemy Engine instance (not connected to a database)
    """
    unix_socket = aurweb.config.get_with_fallback("database", "socket", None)
    kwargs = {
        "username": aurweb.config.get("database", "user"),
        "password": aurweb.config.get_with_fallback("database", "password", None),
        "host": aurweb.config.get("database", "host"),
        "port": aurweb.config.get_with_fallback("database", "port", None),
        "query": {"unix_socket": unix_socket},
    }

    backend = aurweb.config.get("database", "backend")
    driver = aurweb.db.DRIVERS.get(backend)
    return create_engine(URL.create(driver, **kwargs))


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
    try:
        conn.execute(f"CREATE DATABASE {dbname}")
    except ProgrammingError:  # pragma: no cover
        # The database most likely already existed if we hit
        # a ProgrammingError. Just drop the database and try
        # again. If at that point things still fail, any
        # exception will be propogated up to the caller.
        conn.execute(f"DROP DATABASE {dbname}")
        conn.execute(f"CREATE DATABASE {dbname}")
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
    conn.execute(f"DROP DATABASE {dbname}")
    conn.close()


def setup_email():
    # TODO: Fix this data race! This try/catch is ugly; why is it even
    # racing here? Perhaps we need to multiproc + multithread lock
    # inside of setup_database to block the check?
    with Semaphore("/test-emails", flags=O_CREAT, initial_value=1):
        if not os.path.exists(Email.TEST_DIR):
            # Create the directory.
            os.makedirs(Email.TEST_DIR)

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

    if worker_id == "master":  # pragma: no cover
        # If we're not running tests through multiproc pytest-xdist.
        setup_email()
        yield _create_database(engine, dbname)
        _drop_database(engine, dbname)
        return

    def setup(path):
        setup_email()
        _create_database(engine, dbname)

    tmpdir = tmp_path_factory.getbasetemp().parent
    file_lock = FileLock(tmpdir, dbname)
    file_lock.lock(on_create=setup)
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
