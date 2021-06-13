import functools
import math
import re

from sqlalchemy import event

import aurweb.config
import aurweb.util

# See get_engine.
engine = None

# ORM Session class.
Session = None

# Global ORM Session object.
session = None

# Global introspected object memo.
introspected = dict()


def make_random_value(table: str, column: str):
    """ Generate a unique, random value for a string column in a table.

    This can be used to generate for example, session IDs that
    align with the properties of the database column with regards
    to size.

    Internally, we use SQLAlchemy introspection to look at column
    to decide which length to use for random string generation.

    :return: A unique string that is not in the database
    """
    global introspected

    # Make sure column is converted to a string for memo interaction.
    scolumn = str(column)

    # If the target column is not yet introspected, store its introspection
    # object into our global `introspected` memo.
    if scolumn not in introspected:
        from sqlalchemy import inspect
        target_column = scolumn.split('.')[-1]
        col = list(filter(lambda c: c.name == target_column,
                          inspect(table).columns))[0]
        introspected[scolumn] = col

    col = introspected.get(scolumn)
    length = col.type.length

    string = aurweb.util.make_random_string(length)
    while session.query(table).filter(column == string).first():
        string = aurweb.util.make_random_string(length)
    return string


def query(model, *args, **kwargs):
    return session.query(model).filter(*args, **kwargs)


def create(model, autocommit: bool = True, *args, **kwargs):
    instance = model(*args, **kwargs)
    add(instance)
    if autocommit is True:
        commit()
    return instance


def delete(model, *args, autocommit: bool = True, **kwargs):
    instance = session.query(model).filter(*args, **kwargs)
    for record in instance:
        session.delete(record)
    if autocommit is True:
        commit()


def rollback():
    session.rollback()


def add(model):
    session.add(model)
    return model


def commit():
    session.commit()


def get_sqlalchemy_url():
    """
    Build an SQLAlchemy for use with create_engine based on the aurweb configuration.
    """
    import sqlalchemy

    constructor = sqlalchemy.engine.url.URL

    parts = sqlalchemy.__version__.split('.')
    major = int(parts[0])
    minor = int(parts[1])
    if major == 1 and minor >= 4:  # pragma: no cover
        constructor = sqlalchemy.engine.url.URL.create

    aur_db_backend = aurweb.config.get('database', 'backend')
    if aur_db_backend == 'mysql':
        if aurweb.config.get_with_fallback('database', 'port', fallback=None):
            port = aurweb.config.get('database', 'port')
            param_query = None
        else:
            port = None
            param_query = {
                'unix_socket': aurweb.config.get('database', 'socket')
            }
        return constructor(
            'mysql+mysqldb',
            username=aurweb.config.get('database', 'user'),
            password=aurweb.config.get('database', 'password'),
            host=aurweb.config.get('database', 'host'),
            database=aurweb.config.get('database', 'name'),
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


def get_engine(echo: bool = False):
    """
    Return the global SQLAlchemy engine.

    The engine is created on the first call to get_engine and then stored in the
    `engine` global variable for the next calls.
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    global engine, session, Session

    if engine is None:
        connect_args = dict()

        db_backend = aurweb.config.get("database", "backend")
        if db_backend == "sqlite":
            # check_same_thread is for a SQLite technicality
            # https://fastapi.tiangolo.com/tutorial/sql-databases/#note
            connect_args["check_same_thread"] = False

        engine = create_engine(get_sqlalchemy_url(),
                               connect_args=connect_args,
                               echo=echo)

        if db_backend == "sqlite":
            # For SQLite, we need to add some custom functions as
            # they are used in the reference graph method.
            def regexp(regex, item):
                return bool(re.search(regex, str(item)))

            @event.listens_for(engine, "begin")
            def do_begin(conn):
                create_deterministic_function = functools.partial(
                    conn.connection.create_function,
                    deterministic=True
                )
                create_deterministic_function("REGEXP", 2, regexp)

        Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = Session()

    return engine


def kill_engine():
    global engine, Session, session
    if engine:
        session.close()
        engine.dispose()
    engine = Session = session = None


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

    def execute(self, query, params=()):
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
            aur_db_name = aurweb.config.get('database', 'name')
            aur_db_user = aurweb.config.get('database', 'user')
            aur_db_pass = aurweb.config.get('database', 'password')
            aur_db_socket = aurweb.config.get('database', 'socket')
            self._conn = MySQLdb.connect(host=aur_db_host,
                                         user=aur_db_user,
                                         passwd=aur_db_pass,
                                         db=aur_db_name,
                                         unix_socket=aur_db_socket)
        elif aur_db_backend == 'sqlite':
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
