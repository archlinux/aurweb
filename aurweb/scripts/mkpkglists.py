#!/usr/bin/env python3

import datetime
import gzip

import aurweb.config
import aurweb.db

packagesfile = aurweb.config.get('mkpkglists', 'packagesfile')
pkgbasefile = aurweb.config.get('mkpkglists', 'pkgbasefile')
userfile = aurweb.config.get('mkpkglists', 'userfile')


def main():
    conn = aurweb.db.Connection()

    datestr = datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
    pkglist_header = "# AUR package list, generated on " + datestr
    pkgbaselist_header = "# AUR package base list, generated on " + datestr
    userlist_header = "# AUR user name list, generated on " + datestr

    with gzip.open(packagesfile, "w") as f:
        f.write(bytes(pkglist_header + "\n", "UTF-8"))
        cur = conn.execute("SELECT Packages.Name FROM Packages " +
                           "INNER JOIN PackageBases " +
                           "ON PackageBases.ID = Packages.PackageBaseID " +
                           "WHERE PackageBases.PackagerUID IS NOT NULL")
        f.writelines([bytes(x[0] + "\n", "UTF-8") for x in cur.fetchall()])

    with gzip.open(pkgbasefile, "w") as f:
        f.write(bytes(pkgbaselist_header + "\n", "UTF-8"))
        cur = conn.execute("SELECT Name FROM PackageBases " +
                           "WHERE PackagerUID IS NOT NULL")
        f.writelines([bytes(x[0] + "\n", "UTF-8") for x in cur.fetchall()])

    with gzip.open(userfile, "w") as f:
        f.write(bytes(userlist_header + "\n", "UTF-8"))
        cur = conn.execute("SELECT UserName FROM Users")
        f.writelines([bytes(x[0] + "\n", "UTF-8") for x in cur.fetchall()])

    conn.close()


if __name__ == '__main__':
    main()
