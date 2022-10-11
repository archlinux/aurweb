from typing import Iterable

import orjson

from aurweb import config, db
from aurweb.models import Package, PackageBase, User
from aurweb.rpc import RPC

from .base import GitInfo, SpecBase, SpecOutput

ORJSON_OPTS = orjson.OPT_SORT_KEYS | orjson.OPT_INDENT_2


class Spec(SpecBase):
    def __init__(self) -> "Spec":
        self.metadata_repo = GitInfo(
            config.get("git-archive", "metadata-repo"),
        )

    def generate(self) -> Iterable[SpecOutput]:
        # Base query used by the RPC.
        base_query = (
            db.query(Package)
            .join(PackageBase)
            .join(User, PackageBase.MaintainerUID == User.ID, isouter=True)
        )

        # Create an instance of RPC, use it to get entities from
        # our query and perform a metadata subquery for all packages.
        rpc = RPC(version=5, type="info")
        print("performing package database query")
        packages = rpc.entities(base_query).all()
        print("performing package database subqueries")
        rpc.subquery({pkg.ID for pkg in packages})

        pkgbases, pkgnames = dict(), dict()
        for package in packages:
            # Produce RPC type=info data for `package`
            data = rpc.get_info_json_data(package)

            pkgbase_name = data.get("PackageBase")
            pkgbase_data = {
                "ID": data.pop("PackageBaseID"),
                "URLPath": data.pop("URLPath"),
                "FirstSubmitted": data.pop("FirstSubmitted"),
                "LastModified": data.pop("LastModified"),
                "OutOfDate": data.pop("OutOfDate"),
                "Maintainer": data.pop("Maintainer"),
                "Keywords": data.pop("Keywords"),
                "NumVotes": data.pop("NumVotes"),
                "Popularity": data.pop("Popularity"),
                "PopularityUpdated": package.PopularityUpdated.timestamp(),
            }

            # Store the data in `pkgbases` dict. We do this so we only
            # end up processing a single `pkgbase` if repeated after
            # this loop
            pkgbases[pkgbase_name] = pkgbase_data

            # Remove Popularity and NumVotes from package data.
            # These fields change quite often which causes git data
            # modification to explode.
            # data.pop("NumVotes")
            # data.pop("Popularity")

            # Remove the ID key from package json.
            data.pop("ID")

            # Add the `package`.Name to the pkgnames set
            name = data.get("Name")
            pkgnames[name] = data

        # Add metadata outputs
        self.add_output(
            "pkgname.json",
            self.metadata_repo,
            orjson.dumps(pkgnames, option=ORJSON_OPTS),
        )
        self.add_output(
            "pkgbase.json",
            self.metadata_repo,
            orjson.dumps(pkgbases, option=ORJSON_OPTS),
        )

        return self.outputs
