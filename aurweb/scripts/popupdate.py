#!/usr/bin/env python3

import time

import aurweb.db


def main():
    conn = aurweb.db.Connection()
    conn.execute("UPDATE PackageBases SET NumVotes = (" +
                 "SELECT COUNT(*) FROM PackageVotes " +
                 "WHERE PackageVotes.PackageBaseID = PackageBases.ID)")

    now = int(time.time())
    conn.execute("UPDATE PackageBases SET Popularity = (" +
                 "SELECT COALESCE(SUM(POWER(0.98, (? - VoteTS) / 86400)), 0.0) " +
                 "FROM PackageVotes WHERE PackageVotes.PackageBaseID = " +
                 "PackageBases.ID AND NOT VoteTS IS NULL)", [now])

    conn.commit()
    conn.close()


if __name__ == '__main__':
    main()
