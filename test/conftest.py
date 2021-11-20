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
import pytest

from filelock import FileLock
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.engine.base import Engine
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.orm import scoped_session

import aurweb.config
import aurweb.db

from aurweb import initdb, logging, testing

logger = logging.get_logger(__name__)


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
        "password": aurweb.config.get_with_fallback(
            "database", "password", None),
        "host": aurweb.config.get("database", "host"),
        "port": aurweb.config.get_with_fallback("database", "port", None),
        "query": {
            "unix_socket": unix_socket
        }
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
        pass
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


@pytest.fixture(scope="module")
def setup_database(tmp_path_factory: pytest.fixture,
                   worker_id: pytest.fixture) -> None:
    """ Create and drop a database for the suite this fixture is used in. """
    engine = test_engine()
    dbname = aurweb.db.name()

    if worker_id == "master":  # pragma: no cover
        # If we're not running tests through multiproc pytest-xdist.
        yield _create_database(engine, dbname)
        _drop_database(engine, dbname)
        return

    root_tmp_dir = tmp_path_factory.getbasetemp().parent
    fn = root_tmp_dir / dbname

    with FileLock(str(fn) + ".lock"):
        if fn.is_file():
            # If the data file exists, skip database creation.
            yield
        else:
            # Otherwise, create the data file and create the database.
            fn.write_text("1")
            yield _create_database(engine, dbname)
            _drop_database(engine, dbname)


@pytest.fixture(scope="module")
def db_session(setup_database: pytest.fixture) -> scoped_session:
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
