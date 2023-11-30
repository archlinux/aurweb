from sqlalchemy.orm import Session

# Supported database drivers.
DRIVERS = {"postgres": "postgresql+psycopg2"}


class Committer:
    def __init__(self, session):
        self.session = session

    def __enter__(self):
        pass

    def __exit__(self, *args):
        self.session.commit()


def make_random_value(table: str, column: str, length: int):
    """Generate a unique, random value for a string column in a table.

    :return: A unique string that is not in the database
    """
    import aurweb.util

    string = aurweb.util.make_random_string(length)
    while query(table).filter(column == string).first():
        string = aurweb.util.make_random_string(length)
    return string


def test_name() -> str:
    """
    Return the unhashed database name.

    The unhashed database name is determined (lower = higher priority) by:
    -------------------------------------------
    1. {test_suite} portion of PYTEST_CURRENT_TEST
    2. aurweb.config.get("database", "name")

    During `pytest` runs, the PYTEST_CURRENT_TEST environment variable
    is set to the current test in the format `{test_suite}::{test_func}`.

    This allows tests to use a suite-specific database for its runs,
    which decouples database state from test suites.

    :return: Unhashed database name
    """
    import os

    import aurweb.config

    db = os.environ.get("PYTEST_CURRENT_TEST", aurweb.config.get("database", "name"))
    return db.split(":")[0]


def name() -> str:
    """
    Return sanitized database name that can be used for tests or production.

    If test_name() starts with "test/", the database name is SHA-1 hashed,
    prefixed with 'db', and returned. Otherwise, test_name() is passed
    through and not hashed at all.

    :return: SHA1-hashed database name prefixed with 'db'
    """
    dbname = test_name()
    if not dbname.startswith("test/"):
        return dbname

    import hashlib

    sha1 = hashlib.sha1(dbname.encode()).hexdigest()

    return "db" + sha1


# Module-private global memo used to store SQLAlchemy sessions.
_sessions = dict()


def get_session(engine=None) -> Session:
    """Return aurweb.db's global session."""
    dbname = name()

    global _sessions
    if dbname not in _sessions:
        from sqlalchemy.orm import scoped_session, sessionmaker

        if not engine:  # pragma: no cover
            engine = get_engine()

        Session = scoped_session(sessionmaker(autoflush=False, bind=engine))
        _sessions[dbname] = Session()

    return _sessions.get(dbname)


def pop_session(dbname: str) -> None:
    """
    Pop a Session out of the private _sessions memo.

    :param dbname: Database name
    :raises KeyError: When `dbname` does not exist in the memo
    """
    global _sessions
    _sessions.pop(dbname)


def refresh(model):
    """
    Refresh the session's knowledge of `model`.

    :returns: Passed in `model`
    """
    get_session().refresh(model)
    return model


def query(Model, *args, **kwargs):
    """
    Perform an ORM query against the database session.

    This method also runs Query.filter on the resulting model
    query with *args and **kwargs.

    :param Model: Declarative ORM class
    """
    return get_session().query(Model).filter(*args, **kwargs)


def create(Model, *args, **kwargs):
    """
    Create a record and add() it to the database session.

    :param Model: Declarative ORM class
    :return: Model instance
    """
    instance = Model(*args, **kwargs)
    return add(instance)


def delete(model) -> None:
    """
    Delete a set of records found by Query.filter(*args, **kwargs).

    :param Model: Declarative ORM class
    """
    get_session().delete(model)


def delete_all(iterable) -> None:
    """Delete each instance found in `iterable`."""
    import aurweb.util

    session_ = get_session()
    aurweb.util.apply_all(iterable, session_.delete)


def rollback() -> None:
    """Rollback the database session."""
    get_session().rollback()


def add(model):
    """Add `model` to the database session."""
    get_session().add(model)
    return model


def begin():
    """Begin an SQLAlchemy SessionTransaction."""
    return Committer(get_session())


def retry_deadlock(func):
    from sqlalchemy.exc import OperationalError

    def wrapper(*args, _i: int = 0, **kwargs):
        # Retry 10 times, then raise the exception
        # If we fail before the 10th, recurse into `wrapper`
        # If we fail on the 10th, continue to throw the exception
        limit = 10
        try:
            return func(*args, **kwargs)
        except OperationalError as exc:
            if _i < limit and "Deadlock found" in str(exc):
                # Retry on deadlock by recursing into `wrapper`
                return wrapper(*args, _i=_i + 1, **kwargs)
            # Otherwise, just raise the exception
            raise exc

    return wrapper


def async_retry_deadlock(func):
    from sqlalchemy.exc import OperationalError

    async def wrapper(*args, _i: int = 0, **kwargs):
        # Retry 10 times, then raise the exception
        # If we fail before the 10th, recurse into `wrapper`
        # If we fail on the 10th, continue to throw the exception
        limit = 10
        try:
            return await func(*args, **kwargs)
        except OperationalError as exc:
            if _i < limit and "Deadlock found" in str(exc):
                # Retry on deadlock by recursing into `wrapper`
                return await wrapper(*args, _i=_i + 1, **kwargs)
            # Otherwise, just raise the exception
            raise exc

    return wrapper


def get_sqlalchemy_url():
    """
    Build an SQLAlchemy URL for use with create_engine.

    :return: sqlalchemy.engine.url.URL
    """
    import sqlalchemy
    from sqlalchemy.engine.url import URL

    import aurweb.config

    constructor = URL

    parts = sqlalchemy.__version__.split(".")
    major = int(parts[0])
    minor = int(parts[1])
    if (major == 1 and minor >= 4) or (major == 2):  # pragma: no cover
        constructor = URL.create

    aur_db_backend = aurweb.config.get("database", "backend")
    if aur_db_backend == "postgres":
        port = aurweb.config.get_with_fallback("database", "port", None)
        host = aurweb.config.get_with_fallback("database", "host", None)
        socket = None
        if not port:
            socket = aurweb.config.get("database", "socket")
        return constructor(
            DRIVERS.get(aur_db_backend),
            username=aurweb.config.get("database", "user"),
            password=aurweb.config.get_with_fallback(
                "database", "password", fallback=None
            ),
            host=socket if socket else host,
            database=name(),
            port=port,
        )
    elif aur_db_backend == "sqlite":
        return constructor(
            "sqlite",
            database=aurweb.config.get("database", "name"),
        )
    else:
        raise ValueError("unsupported database backend")


def sqlite_regexp(regex, item) -> bool:  # pragma: no cover
    """Method which mimics SQL's REGEXP for SQLite."""
    import re

    return bool(re.search(regex, str(item)))


def setup_sqlite(engine) -> None:  # pragma: no cover
    """Perform setup for an SQLite engine."""
    from sqlalchemy import event

    @event.listens_for(engine, "connect")
    def do_begin(conn, record):
        import functools

        create_deterministic_function = functools.partial(
            conn.create_function, deterministic=True
        )
        create_deterministic_function("REGEXP", 2, sqlite_regexp)


# Module-private global memo used to store SQLAlchemy engines.
_engines = dict()


def get_engine(dbname: str = None, echo: bool = False):
    """
    Return the SQLAlchemy engine for `dbname`.

    The engine is created on the first call to get_engine and then stored in the
    `engine` global variable for the next calls.

    :param dbname: Database name (default: aurweb.db.name())
    :param echo: Flag passed through to sqlalchemy.create_engine
    :return: SQLAlchemy Engine instance
    """
    import aurweb.config

    if not dbname:
        dbname = name()

    global _engines
    if dbname not in _engines:
        db_backend = aurweb.config.get("database", "backend")
        connect_args = dict()

        is_sqlite = bool(db_backend == "sqlite")
        if is_sqlite:  # pragma: no cover
            connect_args["check_same_thread"] = False

        kwargs = {"echo": echo, "connect_args": connect_args}
        from sqlalchemy import create_engine

        _engines[dbname] = create_engine(get_sqlalchemy_url(), **kwargs)

        if is_sqlite:  # pragma: no cover
            setup_sqlite(_engines.get(dbname))

    return _engines.get(dbname)


def pop_engine(dbname: str) -> None:
    """
    Pop an Engine out of the private _engines memo.

    :param dbname: Database name
    :raises KeyError: When `dbname` does not exist in the memo
    """
    global _engines
    _engines.pop(dbname)


def kill_engine() -> None:
    """Close the current session and dispose of the engine."""
    dbname = name()

    session = get_session()
    session.close()
    pop_session(dbname)

    engine = get_engine()
    engine.dispose()
    pop_engine(dbname)


def connect():
    """
    Return an SQLAlchemy connection. Connections are usually pooled. See
    <https://docs.sqlalchemy.org/en/13/core/connections.html>.

    Since SQLAlchemy connections are context managers too, you should use it
    with Python’s `with` operator, or with FastAPI’s dependency injection.
    """
    return get_engine().connect()


class ConnectionExecutor:
    _conn = None
    _paramstyle = None

    def __init__(self, conn, backend=None):
        import aurweb.config

        backend = backend or aurweb.config.get("database", "backend")
        self._conn = conn
        if backend == "postgres":
            self._paramstyle = "format"
        elif backend == "sqlite":
            import sqlite3

            self._paramstyle = sqlite3.paramstyle

    def paramstyle(self):
        return self._paramstyle

    def execute(self, query, params=()):  # pragma: no cover
        # TODO: SQLite support has been removed in FastAPI. It remains
        # here to fund its support for the Sharness testsuite.
        if self._paramstyle in ("format", "pyformat"):
            query = query.replace("%", "%%").replace("?", "%s")
        elif self._paramstyle == "qmark":
            pass
        else:
            raise ValueError("unsupported paramstyle")

        cur = self._conn.cursor()
        cur.execute(query, params)

        return cur

    def commit(self):
        self._conn.commit()

    def close(self):
        self._conn.close()


class Connection:
    _executor = None
    _conn = None

    def __init__(self):
        import aurweb.config

        aur_db_backend = aurweb.config.get("database", "backend")

        if aur_db_backend == "postgres":
            import psycopg2

            aur_db_host = aurweb.config.get_with_fallback("database", "host", None)
            aur_db_name = name()
            aur_db_user = aurweb.config.get("database", "user")
            aur_db_pass = aurweb.config.get_with_fallback("database", "password", str())
            aur_db_socket = aurweb.config.get_with_fallback("database", "socket", None)
            aur_db_port = aurweb.config.get_with_fallback("database", "port", None)
            self._conn = psycopg2.connect(
                host=aur_db_host if not aur_db_socket else aur_db_socket,
                user=aur_db_user,
                password=aur_db_pass,
                dbname=aur_db_name,
                port=aur_db_port if not aur_db_socket else None,
            )
        elif aur_db_backend == "sqlite":  # pragma: no cover
            # TODO: SQLite support has been removed in FastAPI. It remains
            # here to fund its support for Sharness testsuite.
            import math
            import sqlite3

            aur_db_name = aurweb.config.get("database", "name")
            self._conn = sqlite3.connect(aur_db_name)
            self._conn.create_function("POWER", 2, math.pow)
        else:
            raise ValueError("unsupported database backend")

        self._conn = ConnectionExecutor(self._conn, aur_db_backend)

    def execute(self, query, params=()):
        return self._conn.execute(query, params)

    def commit(self):
        self._conn.commit()

    def close(self):
        self._conn.close()
