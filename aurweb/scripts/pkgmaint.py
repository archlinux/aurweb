#!/usr/bin/env python3

import time

import aurweb.db


def main():
    conn = aurweb.db.Connection()

    limit_to = int(time.time()) - 86400
    conn.execute("DELETE FROM PackageBases WHERE " +
                 "SubmittedTS < ? AND PackagerUID IS NULL", [limit_to])

    conn.commit()
    conn.close()


if __name__ == '__main__':
    main()
