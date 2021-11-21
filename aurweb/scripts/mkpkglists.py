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

import gzip
import os
import sys

from collections import defaultdict
from typing import Any, Dict

import orjson

from sqlalchemy import literal, orm

import aurweb.config

from aurweb import db, logging, models, util
from aurweb.benchmark import Benchmark
from aurweb.models import Package, PackageBase, User

logger = logging.get_logger("aurweb.scripts.mkpkglists")

archivedir = aurweb.config.get("mkpkglists", "archivedir")
os.makedirs(archivedir, exist_ok=True)

PACKAGES = aurweb.config.get('mkpkglists', 'packagesfile')
META = aurweb.config.get('mkpkglists', 'packagesmetafile')
META_EXT = aurweb.config.get('mkpkglists', 'packagesmetaextfile')
PKGBASE = aurweb.config.get('mkpkglists', 'pkgbasefile')
USERS = aurweb.config.get('mkpkglists', 'userfile')


TYPE_MAP = {
    "depends": "Depends",
    "makedepends": "MakeDepends",
    "checkdepends": "CheckDepends",
    "optdepends": "OptDepends",
    "conflicts": "Conflicts",
    "provides": "Provides",
    "replaces": "Replaces",
}


def get_extended_dict(query: orm.Query):
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

    data = defaultdict(lambda: defaultdict(list))

    for result in query:
        pkgid = result[0]
        key = TYPE_MAP.get(result[1], result[1])
        output = result[2]
        if result[3]:
            output += result[3]
        data[pkgid][key].append(output)

    return data


def get_extended_fields():
    subqueries = [
        # PackageDependency
        db.query(
            models.PackageDependency
        ).join(models.DependencyType).with_entities(
            models.PackageDependency.PackageID.label("ID"),
            models.DependencyType.Name.label("Type"),
            models.PackageDependency.DepName.label("Name"),
            models.PackageDependency.DepCondition.label("Cond")
        ).distinct().order_by("Name"),

        # PackageRelation
        db.query(
            models.PackageRelation
        ).join(models.RelationType).with_entities(
            models.PackageRelation.PackageID.label("ID"),
            models.RelationType.Name.label("Type"),
            models.PackageRelation.RelName.label("Name"),
            models.PackageRelation.RelCondition.label("Cond")
        ).distinct().order_by("Name"),

        # Groups
        db.query(models.PackageGroup).join(
            models.Group,
            models.PackageGroup.GroupID == models.Group.ID
        ).with_entities(
            models.PackageGroup.PackageID.label("ID"),
            literal("Groups").label("Type"),
            models.Group.Name.label("Name"),
            literal(str()).label("Cond")
        ).distinct().order_by("Name"),

        # Licenses
        db.query(models.PackageLicense).join(
            models.License,
            models.PackageLicense.LicenseID == models.License.ID
        ).with_entities(
            models.PackageLicense.PackageID.label("ID"),
            literal("License").label("Type"),
            models.License.Name.label("Name"),
            literal(str()).label("Cond")
        ).distinct().order_by("Name"),

        # Keywords
        db.query(models.PackageKeyword).join(
            models.Package,
            Package.PackageBaseID == models.PackageKeyword.PackageBaseID
        ).with_entities(
            models.Package.ID.label("ID"),
            literal("Keywords").label("Type"),
            models.PackageKeyword.Keyword.label("Name"),
            literal(str()).label("Cond")
        ).distinct().order_by("Name")
    ]
    query = subqueries[0].union_all(*subqueries[1:])
    return get_extended_dict(query)


EXTENDED_FIELD_HANDLERS = {
    "--extended": get_extended_fields
}


def as_dict(package: Package) -> Dict[str, Any]:
    return {
        "ID": package.ID,
        "Name": package.Name,
        "PackageBaseID": package.PackageBaseID,
        "PackageBase": package.PackageBase,
        "Version": package.Version,
        "Description": package.Description,
        "NumVotes": package.NumVotes,
        "Popularity": float(package.Popularity),
        "OutOfDate": package.OutOfDate,
        "Maintainer": package.Maintainer,
        "FirstSubmitted": package.FirstSubmitted,
        "LastModified": package.LastModified,
    }


def _main():
    bench = Benchmark()
    logger.info("Started re-creating archives, wait a while...")

    query = db.query(Package).join(
        PackageBase,
        PackageBase.ID == Package.PackageBaseID
    ).join(
        User,
        PackageBase.MaintainerUID == User.ID,
        isouter=True
    ).filter(PackageBase.PackagerUID.isnot(None)).with_entities(
        Package.ID,
        Package.Name,
        PackageBase.ID.label("PackageBaseID"),
        PackageBase.Name.label("PackageBase"),
        Package.Version,
        Package.Description,
        PackageBase.NumVotes,
        PackageBase.Popularity,
        PackageBase.OutOfDateTS.label("OutOfDate"),
        User.Username.label("Maintainer"),
        PackageBase.SubmittedTS.label("FirstSubmitted"),
        PackageBase.ModifiedTS.label("LastModified")
    ).distinct().order_by("Name")

    # Produce packages-meta-v1.json.gz
    output = list()
    snapshot_uri = aurweb.config.get("options", "snapshot_uri")
    gzips = {
        "packages": gzip.open(PACKAGES, "wt"),
        "meta": gzip.open(META, "wb"),
    }

    # Append list opening to the metafile.
    gzips["meta"].write(b"[\n")

    # Produce packages.gz + packages-meta-ext-v1.json.gz
    extended = False
    if len(sys.argv) > 1 and sys.argv[1] in EXTENDED_FIELD_HANDLERS:
        gzips["meta_ext"] = gzip.open(META_EXT, "wb")
        # Append list opening to the meta_ext file.
        gzips.get("meta_ext").write(b"[\n")
        f = EXTENDED_FIELD_HANDLERS.get(sys.argv[1])
        data = f()
        extended = True

    results = query.all()
    n = len(results) - 1
    for i, result in enumerate(results):
        # Append to packages.gz.
        gzips.get("packages").write(f"{result.Name}\n")

        # Construct our result JSON dictionary.
        item = as_dict(result)
        item["URLPath"] = snapshot_uri % result.Name

        # We stream out package json objects line per line, so
        # we also need to include the ',' character at the end
        # of package lines (excluding the last package).
        suffix = b",\n" if i < n else b'\n'

        # Write out to packagesmetafile
        output.append(item)
        gzips.get("meta").write(orjson.dumps(output[-1]) + suffix)

        if extended:
            # Write out to packagesmetaextfile.
            data_ = data.get(result.ID, {})
            output[-1].update(data_)
            gzips.get("meta_ext").write(orjson.dumps(output[-1]) + suffix)

    # Append the list closing to meta/meta_ext.
    gzips.get("meta").write(b"]")
    if extended:
        gzips.get("meta_ext").write(b"]")

    # Close gzip files.
    util.apply_all(gzips.values(), lambda gz: gz.close())

    # Produce pkgbase.gz
    query = db.query(PackageBase.Name).filter(
        PackageBase.PackagerUID.isnot(None)).all()
    with gzip.open(PKGBASE, "wt") as f:
        f.writelines([f"{base.Name}\n" for i, base in enumerate(query)])

    # Produce users.gz
    query = db.query(User.Username).all()
    with gzip.open(USERS, "wt") as f:
        f.writelines([f"{user.Username}\n" for i, user in enumerate(query)])

    seconds = util.number_format(bench.end(), 4)
    logger.info(f"Completed in {seconds} seconds.")


def main():
    db.get_engine()
    with db.begin():
        _main()


if __name__ == '__main__':
    main()
