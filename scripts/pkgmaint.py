#!/usr/bin/python3

import aurweb.db


def main():
    conn = aurweb.db.Connection()

    conn.execute("DELETE FROM PackageBases WHERE " +
                 "UNIX_TIMESTAMP() - SubmittedTS > 86400 " +
                 "AND PackagerUID IS NULL")

    conn.commit()
    conn.close()


if __name__ == '__main__':
    main()
