from collections import defaultdict
from typing import Any, Dict, List

from sqlalchemy import and_

import aurweb.config as config

from aurweb import db, models, util
from aurweb.models import dependency_type, relation_type

# Define dependency type mappings from ID to RPC-compatible keys.
DEP_TYPES = {
    dependency_type.DEPENDS_ID: "Depends",
    dependency_type.MAKEDEPENDS_ID: "MakeDepends",
    dependency_type.CHECKDEPENDS_ID: "CheckDepends",
    dependency_type.OPTDEPENDS_ID: "OptDepends"
}

# Define relationship type mappings from ID to RPC-compatible keys.
REL_TYPES = {
    relation_type.CONFLICTS_ID: "Conflicts",
    relation_type.PROVIDES_ID: "Provides",
    relation_type.REPLACES_ID: "Replaces"
}


class RPCError(Exception):
    pass


class RPC:
    """ RPC API handler class.

    There are various pieces to RPC's process, and encapsulating them
    inside of a class means that external users do not abuse the
    RPC implementation to achieve goals. We call type handlers
    by taking a reference to the callback named "_handle_{type}_type(...)",
    and if the handler does not exist, we return a not implemented
    error to the API user.

    EXPOSED_VERSIONS holds the set of versions that the API
    officially supports.

    EXPOSED_TYPES holds the set of types that the API officially
    supports.

    ALIASES holds an alias mapping of type -> type strings.

    We should focus on privatizing implementation helpers and
    focusing on performance in the code used.
    """

    # A set of RPC versions supported by this API.
    EXPOSED_VERSIONS = {5}

    # A set of RPC types supported by this API.
    EXPOSED_TYPES = {
        "info", "multiinfo",
        "search", "msearch",
        "suggest", "suggest-pkgbase"
    }

    # A mapping of aliases.
    ALIASES = {"info": "multiinfo"}

    def __init__(self, version: int = 0, type: str = None):
        self.version = version
        self.type = type

    def error(self, message: str) -> dict:
        return {
            "version": self.version,
            "results": [],
            "resultcount": 0,
            "type": "error",
            "error": message
        }

    def _verify_inputs(self, args: List[str] = []):
        if self.version is None:
            raise RPCError("Please specify an API version.")

        if self.version not in RPC.EXPOSED_VERSIONS:
            raise RPCError("Invalid version specified.")

        if self.type is None or not len(args):
            raise RPCError("No request type/data specified.")

        if self.type not in RPC.EXPOSED_TYPES:
            raise RPCError("Incorrect request type specified.")

        try:
            getattr(self, f"_handle_{self.type.replace('-', '_')}_type")
        except AttributeError:
            raise RPCError(
                f"Request type '{self.type}' is not yet implemented.")

    def _update_json_depends(self, package: models.Package,
                             data: Dict[str, Any]):
        # Walk through all related PackageDependencies and produce
        # the appropriate dict entries.
        for dep in package.package_dependencies:
            if dep.DepTypeID in DEP_TYPES:
                key = DEP_TYPES.get(dep.DepTypeID)

                display = dep.DepName
                if dep.DepCondition:
                    display += dep.DepCondition

                data[key].append(display)

    def _update_json_relations(self, package: models.Package,
                               data: Dict[str, Any]):
        # Walk through all related PackageRelations and produce
        # the appropriate dict entries.
        for rel in package.package_relations:
            if rel.RelTypeID in REL_TYPES:
                key = REL_TYPES.get(rel.RelTypeID)

                display = rel.RelName
                if rel.RelCondition:
                    display += rel.RelCondition

                data[key].append(display)

    def _get_json_data(self, package: models.Package):
        """ Produce dictionary data of one Package that can be JSON-serialized.

        :param package: Package instance
        :returns: JSON-serializable dictionary
        """

        # Produce RPC API compatible Popularity: If zero, it's an integer
        # 0, otherwise, it's formatted to the 6th decimal place.
        pop = package.PackageBase.Popularity
        pop = 0 if not pop else float(util.number_format(pop, 6))

        snapshot_uri = config.get("options", "snapshot_uri")
        data = defaultdict(list)
        data.update({
            "ID": package.ID,
            "Name": package.Name,
            "PackageBaseID": package.PackageBaseID,
            "PackageBase": package.PackageBase.Name,
            # Maintainer should be set following this update if one exists.
            "Maintainer": None,
            "Version": package.Version,
            "Description": package.Description,
            "URL": package.URL,
            "URLPath": snapshot_uri % package.Name,
            "NumVotes": package.PackageBase.NumVotes,
            "Popularity": pop,
            "OutOfDate": package.PackageBase.OutOfDateTS,
            "FirstSubmitted": package.PackageBase.SubmittedTS,
            "LastModified": package.PackageBase.ModifiedTS,
            "License": [
                lic.License.Name for lic in package.package_licenses
            ],
            "Keywords": [
                keyword.Keyword for keyword in package.PackageBase.keywords
            ]
        })

        if package.PackageBase.Maintainer is not None:
            # We do have a maintainer: set the Maintainer key.
            data["Maintainer"] = package.PackageBase.Maintainer.Username

        self._update_json_depends(package, data)
        self._update_json_relations(package, data)
        return data

    def _handle_multiinfo_type(self, args: List[str] = []):
        args = set(args)
        packages = db.query(models.Package).filter(
            models.Package.Name.in_(args))
        return [self._get_json_data(pkg) for pkg in packages]

    def _handle_suggest_pkgbase_type(self, args: List[str] = []):
        records = db.query(models.PackageBase).filter(
            and_(models.PackageBase.PackagerUID.isnot(None),
                 models.PackageBase.Name.like(f"%{args[0]}%"))
        ).order_by(models.PackageBase.Name.asc()).limit(20)
        return [record.Name for record in records]

    def handle(self, args: List[str] = []):
        """ Request entrypoint. A router should pass v, type and args
        to this function and expect an output dictionary to be returned.

        :param v: RPC version argument
        :param type: RPC type argument
        :param args: Deciphered list of arguments based on arg/arg[] inputs
        """
        # Convert type aliased types.
        if self.type in RPC.ALIASES:
            self.type = RPC.ALIASES.get(self.type)

        # Prepare our output data dictionary with some basic keys.
        data = {"version": self.version, "type": self.type}

        # Run some verification on our given arguments.
        try:
            self._verify_inputs(args)
        except RPCError as exc:
            return self.error(str(exc))

        # Get a handle to our callback and trap an RPCError with
        # an empty list of results based on callback's execution.
        callback = getattr(self, f"_handle_{self.type.replace('-', '_')}_type")
        results = callback(args)

        # These types are special: we produce a different kind of
        # successful JSON output: a list of results.
        if self.type in ("suggest", "suggest-pkgbase"):
            return results

        # Return JSON output.
        data.update({
            "resultcount": len(results),
            "results": results
        })
        return data
