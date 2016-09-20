#!/usr/bin/python3

import datetime
import gzip
import os

import aurweb.db

docroot = os.path.dirname(os.path.realpath(__file__)) + "/../web/html/"


def main():
    conn = aurweb.db.Connection()

    datestr = datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
    pkglist_header = "# AUR package list, generated on " + datestr
    pkgbaselist_header = "# AUR package base list, generated on " + datestr

    with gzip.open(docroot + "packages.gz", "w") as f:
        f.write(bytes(pkglist_header + "\n", "UTF-8"))
        cur = conn.execute("SELECT Packages.Name FROM Packages " +
                           "INNER JOIN PackageBases " +
                           "ON PackageBases.ID = Packages.PackageBaseID " +
                           "WHERE PackageBases.PackagerUID IS NOT NULL")
        f.writelines([bytes(x[0] + "\n", "UTF-8") for x in cur.fetchall()])

    with gzip.open(docroot + "pkgbase.gz", "w") as f:
        f.write(bytes(pkgbaselist_header + "\n", "UTF-8"))
        cur = conn.execute("SELECT Name FROM PackageBases " +
                           "WHERE PackagerUID IS NOT NULL")
        f.writelines([bytes(x[0] + "\n", "UTF-8") for x in cur.fetchall()])

    conn.close()


if __name__ == '__main__':
    main()
