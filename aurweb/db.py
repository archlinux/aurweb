import mysql.connector
import sqlite3

import aurweb.config


class Connection:
    _conn = None
    _paramstyle = None

    def __init__(self):
        aur_db_backend = aurweb.config.get('database', 'backend')

        if aur_db_backend == 'mysql':
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
            aur_db_name = aurweb.config.get('database', 'name')
            self._conn = sqlite3.connect(aur_db_name)
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
