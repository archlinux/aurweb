import math

import aurweb.config

engine = None  # See get_engine

# ORM Session class.
Session = None

# Global ORM Session object.
session = None


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
        return constructor(
            'mysql+mysqlconnector',
            username=aurweb.config.get('database', 'user'),
            password=aurweb.config.get('database', 'password'),
            host=aurweb.config.get('database', 'host'),
            database=aurweb.config.get('database', 'name'),
            query={
                'unix_socket': aurweb.config.get('database', 'socket'),
            },
        )
    elif aur_db_backend == 'sqlite':
        return constructor(
            'sqlite',
            database=aurweb.config.get('database', 'name'),
        )
    else:
        raise ValueError('unsupported database backend')


def get_engine():
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
        if aurweb.config.get("database", "backend") == "sqlite":
            # check_same_thread is for a SQLite technicality
            # https://fastapi.tiangolo.com/tutorial/sql-databases/#note
            connect_args["check_same_thread"] = False
        engine = create_engine(get_sqlalchemy_url(), connect_args=connect_args)
        Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = Session()

    return engine


def connect():
    """
    Return an SQLAlchemy connection. Connections are usually pooled. See
    <https://docs.sqlalchemy.org/en/13/core/connections.html>.

    Since SQLAlchemy connections are context managers too, you should use it
    with Python’s `with` operator, or with FastAPI’s dependency injection.
    """
    return get_engine().connect()


class Connection:
    _conn = None
    _paramstyle = None

    def __init__(self):
        aur_db_backend = aurweb.config.get('database', 'backend')

        if aur_db_backend == 'mysql':
            import mysql.connector
            aur_db_host = aurweb.config.get('database', 'host')
            aur_db_name = aurweb.config.get('database', 'name')
            aur_db_user = aurweb.config.get('database', 'user')
            aur_db_pass = aurweb.config.get('database', 'password')
            aur_db_socket = aurweb.config.get('database', 'socket')
            self._conn = mysql.connector.connect(host=aur_db_host,
                                                 user=aur_db_user,
                                                 passwd=aur_db_pass,
                                                 db=aur_db_name,
                                                 unix_socket=aur_db_socket,
                                                 buffered=True)
            self._paramstyle = mysql.connector.paramstyle
        elif aur_db_backend == 'sqlite':
            import sqlite3
            aur_db_name = aurweb.config.get('database', 'name')
            self._conn = sqlite3.connect(aur_db_name)
            self._conn.create_function("POWER", 2, math.pow)
            self._paramstyle = sqlite3.paramstyle
        else:
            raise ValueError('unsupported database backend')

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
