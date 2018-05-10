#!/usr/bin/env python3

import time

import aurweb.db


def main():
    conn = aurweb.db.Connection()

    limit_to = int(time.time()) - 86400 * 7
    conn.execute("UPDATE Users SET LastLoginIPAddress = NULL " +
                 "WHERE LastLogin < ?", [limit_to])
    conn.execute("UPDATE Users SET LastSSHLoginIPAddress = NULL " +
                 "WHERE LastSSHLogin < ?", [limit_to])

    conn.commit()
    conn.close()


if __name__ == '__main__':
    main()
