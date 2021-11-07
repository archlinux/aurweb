#!/usr/bin/env python3
"""
Produces package, package base and user archives for the AUR
database.

Archives:

    packages.gz               | A line-separated list of package names
    packages-meta-v1.json     | A type=search RPC-formatted JSON dataset
    packages-meta-ext-v1.json | An --extended archive
    pkgbase.gz                | A line-separated list of package base names
    users.gz                  | A line-separated list of user names

This script takes an optional argument: --extended. Based
on the following, right-hand side fields are added to each item.

    --extended  | License, Keywords, Groups, relations and dependencies

"""

import datetime
import gzip
import sys

from collections import defaultdict
from decimal import Decimal

import orjson

import aurweb.config
import aurweb.db

packagesfile = aurweb.config.get('mkpkglists', 'packagesfile')
packagesmetafile = aurweb.config.get('mkpkglists', 'packagesmetafile')
packagesmetaextfile = aurweb.config.get('mkpkglists', 'packagesmetaextfile')

pkgbasefile = aurweb.config.get('mkpkglists', 'pkgbasefile')

userfile = aurweb.config.get('mkpkglists', 'userfile')


TYPE_MAP = {
    "depends": "Depends",
    "makedepends": "MakeDepends",
    "checkdepends": "CheckDepends",
    "optdepends": "OptDepends",
    "conflicts": "Conflicts",
    "provides": "Provides",
    "replaces": "Replaces",
}


def get_extended_dict(query: str):
    """
    Produce data in the form in a single bulk SQL query:

    {
        <integer_package_id>: {
            "Depends": [...],
            "Conflicts": [...],
            "License": [...]
        }
    }

    The caller can then use this data to populate a dataset of packages.

    output = produce_base_output_data()
    data = get_extended_dict(query)
    for i in range(len(output)):
        package_id = output[i].get("ID")
        output[i].update(data.get(package_id))
    """

    conn = aurweb.db.Connection()

    cursor = conn.execute(query)

    data = defaultdict(lambda: defaultdict(list))

    for result in cursor.fetchall():

        pkgid = result[0]
        key = TYPE_MAP.get(result[1])
        output = result[2]
        if result[3]:
            output += result[3]

        # In all cases, we have at least an empty License list.
        if "License" not in data[pkgid]:
            data[pkgid]["License"] = []

        # In all cases, we have at least an empty Keywords list.
        if "Keywords" not in data[pkgid]:
            data[pkgid]["Keywords"] = []

        data[pkgid][key].append(output)

    conn.close()
    return data


def get_extended_fields():
    # Returns: [ID, Type, Name, Cond]
    query = """
    SELECT PackageDepends.PackageID AS ID, DependencyTypes.Name AS Type,
           PackageDepends.DepName AS Name, PackageDepends.DepCondition AS Cond
    FROM PackageDepends
    LEFT JOIN DependencyTypes
    ON DependencyTypes.ID = PackageDepends.DepTypeID
    UNION SELECT PackageRelations.PackageID AS ID, RelationTypes.Name AS Type,
          PackageRelations.RelName AS Name,
          PackageRelations.RelCondition AS Cond
    FROM PackageRelations
    LEFT JOIN RelationTypes
    ON RelationTypes.ID = PackageRelations.RelTypeID
    UNION SELECT PackageGroups.PackageID AS ID, 'Groups' AS Type,
          Groups.Name, '' AS Cond
    FROM Groups
    INNER JOIN PackageGroups ON PackageGroups.GroupID = Groups.ID
    UNION SELECT PackageLicenses.PackageID AS ID, 'License' AS Type,
          Licenses.Name, '' as Cond
    FROM Licenses
    INNER JOIN PackageLicenses ON PackageLicenses.LicenseID = Licenses.ID
    UNION SELECT Packages.ID AS ID, 'Keywords' AS Type,
          PackageKeywords.Keyword AS Name, '' as Cond
    FROM PackageKeywords
    INNER JOIN Packages ON Packages.PackageBaseID = PackageKeywords.PackageBaseID
    """
    return get_extended_dict(query)


EXTENDED_FIELD_HANDLERS = {
    "--extended": get_extended_fields
}


def is_decimal(column):
    """ Check if an SQL column is of decimal.Decimal type. """
    if isinstance(column, Decimal):
        return float(column)
    return column


def write_archive(archive: str, output: list):
    with gzip.open(archive, "wb") as f:
        f.write(b"[\n")
        for i, item in enumerate(output):
            f.write(orjson.dumps(item))
            if i < len(output) - 1:
                f.write(b",")
            f.write(b"\n")
        f.write(b"]")


def main():
    conn = aurweb.db.Connection()

    datestr = datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
    pkglist_header = "# AUR package list, generated on " + datestr
    pkgbaselist_header = "# AUR package base list, generated on " + datestr
    userlist_header = "# AUR user name list, generated on " + datestr

    # Query columns; copied from RPC.
    columns = ("Packages.ID, Packages.Name, "
               "PackageBases.ID AS PackageBaseID, "
               "PackageBases.Name AS PackageBase, "
               "Version, Description, URL, NumVotes, "
               "Popularity, OutOfDateTS AS OutOfDate, "
               "Users.UserName AS Maintainer, "
               "SubmittedTS AS FirstSubmitted, "
               "ModifiedTS AS LastModified")

    # Perform query.
    cur = conn.execute(f"SELECT {columns} FROM Packages "
                       "LEFT JOIN PackageBases "
                       "ON PackageBases.ID = Packages.PackageBaseID "
                       "LEFT JOIN Users "
                       "ON PackageBases.MaintainerUID = Users.ID "
                       "WHERE PackageBases.PackagerUID IS NOT NULL")

    # Produce packages-meta-v1.json.gz
    output = list()
    snapshot_uri = aurweb.config.get("options", "snapshot_uri")
    for result in cur.fetchall():
        item = {
            column[0]: is_decimal(result[i])
            for i, column in enumerate(cur.description)
        }
        item["URLPath"] = snapshot_uri % item.get("Name")
        output.append(item)

    write_archive(packagesmetafile, output)

    # Produce packages-meta-ext-v1.json.gz
    if len(sys.argv) > 1 and sys.argv[1] in EXTENDED_FIELD_HANDLERS:
        f = EXTENDED_FIELD_HANDLERS.get(sys.argv[1])
        data = f()

        default_ = {"Groups": [], "License": [], "Keywords": []}
        for i in range(len(output)):
            data_ = data.get(output[i].get("ID"), default_)
            output[i].update(data_)

        write_archive(packagesmetaextfile, output)

    # Produce packages.gz
    with gzip.open(packagesfile, "wb") as f:
        f.write(bytes(pkglist_header + "\n", "UTF-8"))
        f.writelines([
            bytes(x.get("Name") + "\n", "UTF-8")
            for x in output
        ])

    # Produce pkgbase.gz
    with gzip.open(pkgbasefile, "w") as f:
        f.write(bytes(pkgbaselist_header + "\n", "UTF-8"))
        cur = conn.execute("SELECT Name FROM PackageBases " +
                           "WHERE PackagerUID IS NOT NULL")
        f.writelines([bytes(x[0] + "\n", "UTF-8") for x in cur.fetchall()])

    # Produce users.gz
    with gzip.open(userfile, "w") as f:
        f.write(bytes(userlist_header + "\n", "UTF-8"))
        cur = conn.execute("SELECT UserName FROM Users")
        f.writelines([bytes(x[0] + "\n", "UTF-8") for x in cur.fetchall()])

    conn.close()


if __name__ == '__main__':
    main()
