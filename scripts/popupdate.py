#!/usr/bin/python3

import aurweb.db


def main():
    conn = aurweb.db.Connection()

    conn.execute("UPDATE PackageBases SET NumVotes = (" +
                 "SELECT COUNT(*) FROM PackageVotes " +
                 "WHERE PackageVotes.PackageBaseID = PackageBases.ID)")

    conn.execute("UPDATE PackageBases SET Popularity = (" +
                 "SELECT COALESCE(SUM(POWER(0.98, (UNIX_TIMESTAMP() - VoteTS) / 86400)), 0.0) " +
                 "FROM PackageVotes WHERE PackageVotes.PackageBaseID = " +
                 "PackageBases.ID AND NOT VoteTS IS NULL)")

    conn.commit()
    conn.close()


if __name__ == '__main__':
    main()
