#!/usr/bin/env python3

from datetime import datetime

import aurweb.db


def run_single(conn, pkgbase):
    """ A single popupdate. The given pkgbase instance will be
    refreshed after the database update is done.

    NOTE: This function is compatible only with aurweb FastAPI.

    :param conn: db.Connection[Executor]
    :param pkgbase: Instance of db.PackageBase
    """

    conn.execute("UPDATE PackageBases SET NumVotes = ("
                 "SELECT COUNT(*) FROM PackageVotes "
                 "WHERE PackageVotes.PackageBaseID = PackageBases.ID) "
                 "WHERE PackageBases.ID = ?", [pkgbase.ID])

    now = int(datetime.utcnow().timestamp())
    conn.execute("UPDATE PackageBases SET Popularity = ("
                 "SELECT COALESCE(SUM(POWER(0.98, (? - VoteTS) / 86400)), 0.0) "
                 "FROM PackageVotes WHERE PackageVotes.PackageBaseID = "
                 "PackageBases.ID AND NOT VoteTS IS NULL) WHERE "
                 "PackageBases.ID = ?", [now, pkgbase.ID])

    conn.commit()
    conn.close()
    aurweb.db.refresh(pkgbase)


def main():
    conn = aurweb.db.Connection()
    conn.execute("UPDATE PackageBases SET NumVotes = ("
                 "SELECT COUNT(*) FROM PackageVotes "
                 "WHERE PackageVotes.PackageBaseID = PackageBases.ID)")

    now = int(datetime.utcnow().timestamp())
    conn.execute("UPDATE PackageBases SET Popularity = ("
                 "SELECT COALESCE(SUM(POWER(0.98, (? - VoteTS) / 86400)), 0.0) "
                 "FROM PackageVotes WHERE PackageVotes.PackageBaseID = "
                 "PackageBases.ID AND NOT VoteTS IS NULL)", [now])

    conn.commit()
    conn.close()


if __name__ == '__main__':
    main()
