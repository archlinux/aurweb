import mysql.connector

import config


class Connection:
    _conn = None

    def __init__(self):
        aur_db_host = config.get('database', 'host')
        aur_db_name = config.get('database', 'name')
        aur_db_user = config.get('database', 'user')
        aur_db_pass = config.get('database', 'password')
        aur_db_socket = config.get('database', 'socket')

        self._conn = mysql.connector.connect(host=aur_db_host,
                                             user=aur_db_user,
                                             passwd=aur_db_pass,
                                             db=aur_db_name,
                                             unix_socket=aur_db_socket,
                                             buffered=True)

    def execute(self, query, params=()):
        query = query.replace('%', '%%').replace('?', '%s')

        cur = self._conn.cursor()
        cur.execute(query, params)

        return cur

    def commit(self):
        self._conn.commit()

    def close(self):
        self._conn.close()
