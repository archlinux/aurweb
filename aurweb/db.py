import functools
import hashlib
import math
import os
import re

from typing import Iterable, NewType

import sqlalchemy

from sqlalchemy import create_engine, event
from sqlalchemy.engine.base import Engine
from sqlalchemy.engine.url import URL
from sqlalchemy.orm import Query, Session, SessionTransaction, scoped_session, sessionmaker

import aurweb.config
import aurweb.util

from aurweb import logging

logger = logging.get_logger(__name__)

DRIVERS = {
    "mysql": "mysql+mysqldb"
}

# Some types we don't get access to in this module.
Base = NewType("Base", "aurweb.models.declarative_base.Base")


def make_random_value(table: str, column: str, length: int):
    """ Generate a unique, random value for a string column in a table.

    :return: A unique string that is not in the database
    """
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
    db = os.environ.get("PYTEST_CURRENT_TEST",
                        aurweb.config.get("database", "name"))
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
    sha1 = hashlib.sha1(dbname.encode()).hexdigest()
    return "db" + sha1


# Module-private global memo used to store SQLAlchemy sessions.
_sessions = dict()


def get_session(engine: Engine = None) -> Session:
    """ Return aurweb.db's global session. """
    dbname = name()

    global _sessions
    if dbname not in _sessions:

        if not engine:  # pragma: no cover
            engine = get_engine()

        Session = scoped_session(
            sessionmaker(autocommit=True, autoflush=False, bind=engine))
        _sessions[dbname] = Session()

        # If this is the first grab of this session, log out the
        # database name used.
        raw_dbname = test_name()
        logger.debug(f"DBName({raw_dbname}): {dbname}")

    return _sessions.get(dbname)


def pop_session(dbname: str) -> None:
    """
    Pop a Session out of the private _sessions memo.

    :param dbname: Database name
    :raises KeyError: When `dbname` does not exist in the memo
    """
    global _sessions
    _sessions.pop(dbname)


def refresh(model: Base) -> Base:
    """ Refresh the session's knowledge of `model`. """
    get_session().refresh(model)
    return model


def query(Model: Base, *args, **kwargs) -> Query:
    """
    Perform an ORM query against the database session.

    This method also runs Query.filter on the resulting model
    query with *args and **kwargs.

    :param Model: Declarative ORM class
    """
    return get_session().query(Model).filter(*args, **kwargs)


def create(Model: Base, *args, **kwargs) -> Base:
    """
    Create a record and add() it to the database session.

    :param Model: Declarative ORM class
    :return: Model instance
    """
    instance = Model(*args, **kwargs)
    return add(instance)


def delete(model: Base) -> None:
    """
    Delete a set of records found by Query.filter(*args, **kwargs).

    :param Model: Declarative ORM class
    """
    get_session().delete(model)


def delete_all(iterable: Iterable) -> None:
    """ Delete each instance found in `iterable`. """
    session_ = get_session()
    aurweb.util.apply_all(iterable, session_.delete)


def rollback() -> None:
    """ Rollback the database session. """
    get_session().rollback()


def add(model: Base) -> Base:
    """ Add `model` to the database session. """
    get_session().add(model)
    return model


def begin() -> SessionTransaction:
    """ Begin an SQLAlchemy SessionTransaction. """
    return get_session().begin()


def get_sqlalchemy_url() -> URL:
    """
    Build an SQLAlchemy URL for use with create_engine.

    :return: sqlalchemy.engine.url.URL
    """
    constructor = URL

    parts = sqlalchemy.__version__.split('.')
    major = int(parts[0])
    minor = int(parts[1])
    if major == 1 and minor >= 4:  # pragma: no cover
        constructor = URL.create

    aur_db_backend = aurweb.config.get('database', 'backend')
    if aur_db_backend == 'mysql':
        param_query = {}
        port = aurweb.config.get_with_fallback("database", "port", None)
        if not port:
            param_query["unix_socket"] = aurweb.config.get(
                "database", "socket")

        return constructor(
            DRIVERS.get(aur_db_backend),
            username=aurweb.config.get('database', 'user'),
            password=aurweb.config.get_with_fallback('database', 'password',
                                                     fallback=None),
            host=aurweb.config.get('database', 'host'),
            database=name(),
            port=port,
            query=param_query
        )
    elif aur_db_backend == 'sqlite':
        return constructor(
            'sqlite',
            database=aurweb.config.get('database', 'name'),
        )
    else:
        raise ValueError('unsupported database backend')


def sqlite_regexp(regex, item) -> bool:  # pragma: no cover
    """ Method which mimics SQL's REGEXP for SQLite. """
    return bool(re.search(regex, str(item)))


def setup_sqlite(engine: Engine) -> None:  # pragma: no cover
    """ Perform setup for an SQLite engine. """
    @event.listens_for(engine, "connect")
    def do_begin(conn, record):
        create_deterministic_function = functools.partial(
            conn.create_function,
            deterministic=True
        )
        create_deterministic_function("REGEXP", 2, sqlite_regexp)


# Module-private global memo used to store SQLAlchemy engines.
_engines = dict()


def get_engine(dbname: str = None, echo: bool = False) -> Engine:
    """
    Return the SQLAlchemy engine for `dbname`.

    The engine is created on the first call to get_engine and then stored in the
    `engine` global variable for the next calls.

    :param dbname: Database name (default: aurweb.db.name())
    :param echo: Flag passed through to sqlalchemy.create_engine
    :return: SQLAlchemy Engine instance
    """
    if not dbname:
        dbname = name()

    global _engines
    if dbname not in _engines:
        db_backend = aurweb.config.get("database", "backend")
        connect_args = dict()

        is_sqlite = bool(db_backend == "sqlite")
        if is_sqlite:  # pragma: no cover
            connect_args["check_same_thread"] = False

        kwargs = {
            "echo": echo,
            "connect_args": connect_args
        }
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
    """ Close the current session and dispose of the engine. """
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

    def __init__(self, conn, backend=aurweb.config.get("database", "backend")):
        self._conn = conn
        if backend == "mysql":
            self._paramstyle = "format"
        elif backend == "sqlite":
            import sqlite3
            self._paramstyle = sqlite3.paramstyle

    def paramstyle(self):
        return self._paramstyle

    def execute(self, query, params=()):  # pragma: no cover
        # TODO: SQLite support has been removed in FastAPI. It remains
        # here to fund its support for PHP until it is removed.
        if self._paramstyle in ('format', 'pyformat'):
            query = query.replace('%', '%%').replace('?', '%s')
        elif self._paramstyle == 'qmark':
            pass
        else:
            raise ValueError('unsupported paramstyle')

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
        aur_db_backend = aurweb.config.get('database', 'backend')

        if aur_db_backend == 'mysql':
            import MySQLdb
            aur_db_host = aurweb.config.get('database', 'host')
            aur_db_name = name()
            aur_db_user = aurweb.config.get('database', 'user')
            aur_db_pass = aurweb.config.get_with_fallback(
                'database', 'password', str())
            aur_db_socket = aurweb.config.get('database', 'socket')
            self._conn = MySQLdb.connect(host=aur_db_host,
                                         user=aur_db_user,
                                         passwd=aur_db_pass,
                                         db=aur_db_name,
                                         unix_socket=aur_db_socket)
        elif aur_db_backend == 'sqlite':  # pragma: no cover
            # TODO: SQLite support has been removed in FastAPI. It remains
            # here to fund its support for PHP until it is removed.
            import sqlite3
            aur_db_name = aurweb.config.get('database', 'name')
            self._conn = sqlite3.connect(aur_db_name)
            self._conn.create_function("POWER", 2, math.pow)
        else:
            raise ValueError('unsupported database backend')

        self._conn = ConnectionExecutor(self._conn, aur_db_backend)

    def execute(self, query, params=()):
        return self._conn.execute(query, params)

    def commit(self):
        self._conn.commit()

    def close(self):
        self._conn.close()
