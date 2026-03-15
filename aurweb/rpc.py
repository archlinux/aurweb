import os
from collections import defaultdict
from typing import Any, Callable, NewType, Union

from fastapi.responses import HTMLResponse
from sqlalchemy import and_, literal, orm, select

import aurweb.config as config
from aurweb import db, defaults, models, time
from aurweb.exceptions import RPCError
from aurweb.filters import number_format
from aurweb.models.package_base import popularity
from aurweb.packages.search import RPCSearch

TYPE_MAPPING = {
    "depends": "Depends",
    "makedepends": "MakeDepends",
    "checkdepends": "CheckDepends",
    "optdepends": "OptDepends",
    "conflicts": "Conflicts",
    "provides": "Provides",
    "replaces": "Replaces",
}

DataGenerator = NewType("DataGenerator", Callable[[models.Package], dict[str, Any]])


def documentation():
    aurwebdir = config.get("options", "aurwebdir")
    rpc_doc = os.path.join(aurwebdir, "doc", "rpc.html")

    if not os.path.exists(rpc_doc):
        raise OSError("doc/rpc.html could not be read")

    with open(rpc_doc) as f:
        data = f.read()
    return HTMLResponse(data)


class RPC:
    """RPC API handler class.

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
        "info",
        "multiinfo",
        "search",
        "msearch",
        "suggest",
        "suggest-pkgbase",
    }

    # A mapping of type aliases.
    TYPE_ALIASES = {"info": "multiinfo"}

    EXPOSED_BYS = {
        "name-desc",
        "name",
        "maintainer",
        "depends",
        "makedepends",
        "optdepends",
        "checkdepends",
        "provides",
        "conflicts",
        "replaces",
        "groups",
        "submitter",
        "keywords",
        "comaintainers",
    }

    # A mapping of by aliases.
    BY_ALIASES = {
        "name-desc": "nd",
        "name": "n",
        "maintainer": "m",
        "submitter": "s",
        "keywords": "k",
        "comaintainers": "c",
    }

    def __init__(self, version: int = 0, type: str | None = None) -> None:
        self.version = version
        self.type = RPC.TYPE_ALIASES.get(type, type)

    def error(self, message: str) -> dict[str, Any]:
        return {
            "version": self.version,
            "results": [],
            "resultcount": 0,
            "type": "error",
            "error": message,
        }

    def _verify_inputs(self, by: str = [], args: list[str] = []) -> None:
        if self.version is None:
            raise RPCError("Please specify an API version.")

        if self.version not in RPC.EXPOSED_VERSIONS:
            raise RPCError("Invalid version specified.")

        if by not in RPC.EXPOSED_BYS:
            raise RPCError("Incorrect by field specified.")

        if self.type is None:
            raise RPCError("No request type/data specified.")

        if self.type not in RPC.EXPOSED_TYPES:
            raise RPCError("Incorrect request type specified.")

    def _enforce_args(self, args: list[str]) -> None:
        if not args:
            raise RPCError("No request type/data specified.")

    def get_json_data(self, package: models.Package) -> dict[str, Any]:
        """Produce dictionary data of one Package that can be JSON-serialized.

        :param package: Package instance
        :returns: JSON-serializable dictionary
        """

        # Normalize Popularity for RPC output to 6 decimal precision
        pop = popularity(package, time.utcnow())
        pop = 0 if not pop else float(number_format(pop, 6))

        snapshot_uri = config.get("options", "snapshot_uri")
        return {
            "ID": package.ID,
            "Name": package.Name,
            "PackageBaseID": package.PackageBaseID,
            "PackageBase": package.PackageBaseName,
            # Maintainer should be set following this update if one exists.
            "Maintainer": package.Maintainer,
            "Submitter": package.Submitter,
            "Version": package.Version,
            "Description": package.Description,
            "URL": package.URL,
            "URLPath": snapshot_uri % package.PackageBaseName,
            "NumVotes": package.NumVotes,
            "Popularity": pop,
            "OutOfDate": package.OutOfDateTS,
            "FirstSubmitted": package.SubmittedTS,
            "LastModified": package.ModifiedTS,
        }

    def get_info_json_data(self, package: models.Package) -> dict[str, Any]:
        data = self.get_json_data(package)

        # All info results have _at least_ an empty list of
        # License and Keywords.
        data.update({"License": [], "Keywords": []})

        # If we actually got extra_info records, update data with
        # them for this particular package.
        if self.extra_info:
            data.update(self.extra_info.get(package.ID, {}))

        return data

    def _assemble_json_data(
        self, packages: list[models.Package], data_generator: DataGenerator
    ) -> list[dict[str, Any]]:
        """
        Assemble JSON data out of a list of packages.

        :param packages: A list of Package instances or a Package ORM query
        :param data_generator: Generator callable of single-Package JSON data
        """
        return [data_generator(pkg) for pkg in packages]

    def entities(self, query):
        """Select specific RPC columns on `query`."""
        Submitter = orm.aliased(models.User)

        cols = (
            models.Package.ID,
            models.Package.Name,
            models.Package.Version,
            models.Package.Description,
            models.Package.URL,
            models.Package.PackageBaseID,
            models.PackageBase.Name.label("PackageBaseName"),
            models.PackageBase.NumVotes,
            models.PackageBase.Popularity,
            models.PackageBase.PopularityUpdated,
            models.PackageBase.OutOfDateTS,
            models.PackageBase.SubmittedTS,
            models.PackageBase.ModifiedTS,
            models.User.Username.label("Maintainer"),
            Submitter.Username.label("Submitter"),
        )

        q = query.join(
            Submitter,
            Submitter.ID == models.PackageBase.SubmitterUID,
            isouter=True,
        )

        # Legacy orm.Query uses with_entities(); SA 2.0 Select uses
        # with_only_columns().  PackageSearch still yields a legacy Query,
        # so we keep both paths until that module is migrated.
        if isinstance(q, orm.Query):
            return q.with_entities(*cols).group_by(models.Package.ID)
        return q.with_only_columns(*cols).group_by(models.Package.ID)

    def subquery(self, ids: set[int]):
        Package = models.Package
        PackageKeyword = models.PackageKeyword

        subqueries = [
            # PackageDependency
            select(
                models.PackageDependency.PackageID.label("ID"),
                models.DependencyType.Name.label("Type"),
                models.PackageDependency.DepName.label("Name"),
                models.PackageDependency.DepCondition.label("Cond"),
            )
            .select_from(models.PackageDependency)
            .join(models.DependencyType)
            .where(models.PackageDependency.PackageID.in_(ids))
            .distinct()
            .order_by("Name"),
            # PackageRelation
            select(
                models.PackageRelation.PackageID.label("ID"),
                models.RelationType.Name.label("Type"),
                models.PackageRelation.RelName.label("Name"),
                models.PackageRelation.RelCondition.label("Cond"),
            )
            .select_from(models.PackageRelation)
            .join(models.RelationType)
            .where(models.PackageRelation.PackageID.in_(ids))
            .distinct()
            .order_by("Name"),
            # Groups
            select(
                models.PackageGroup.PackageID.label("ID"),
                literal("Groups").label("Type"),
                models.Group.Name.label("Name"),
                literal(str()).label("Cond"),
            )
            .select_from(models.PackageGroup)
            .join(
                models.Group,
                and_(
                    models.PackageGroup.GroupID == models.Group.ID,
                    models.PackageGroup.PackageID.in_(ids),
                ),
            )
            .distinct()
            .order_by("Name"),
            # Licenses
            select(
                models.PackageLicense.PackageID.label("ID"),
                literal("License").label("Type"),
                models.License.Name.label("Name"),
                literal(str()).label("Cond"),
            )
            .select_from(models.PackageLicense)
            .join(models.License, models.PackageLicense.LicenseID == models.License.ID)
            .where(models.PackageLicense.PackageID.in_(ids))
            .distinct()
            .order_by("Name"),
            # Keywords
            select(
                Package.ID.label("ID"),
                literal("Keywords").label("Type"),
                PackageKeyword.Keyword.label("Name"),
                literal(str()).label("Cond"),
            )
            .select_from(PackageKeyword)
            .join(
                Package,
                and_(
                    Package.PackageBaseID == PackageKeyword.PackageBaseID,
                    Package.ID.in_(ids),
                ),
            )
            .distinct()
            .order_by("Name"),
            # Co-Maintainer
            select(
                Package.ID,
                literal("CoMaintainers").label("Type"),
                models.User.Username.label("Name"),
                literal(str()).label("Cond"),
            )
            .select_from(models.PackageComaintainer)
            .join(models.User, models.User.ID == models.PackageComaintainer.UsersID)
            .join(
                Package,
                Package.PackageBaseID == models.PackageComaintainer.PackageBaseID,
            )
            .distinct()  # A package could have the same co-maintainer multiple times
            .order_by("Name"),
        ]

        # Union all subqueries together and execute.
        combined = subqueries[0].union_all(*subqueries[1:])
        query = db.get_session().execute(combined).all()

        # Store our extra information in a class-wise dictionary,
        # which contains package id -> extra info dict mappings.
        self.extra_info = defaultdict(lambda: defaultdict(list))
        for record in query:
            type_ = TYPE_MAPPING.get(record.Type, record.Type)

            name = record.Name
            if record.Cond:
                name += record.Cond

            self.extra_info[record.ID][type_].append(name)

    def _handle_multiinfo_type(
        self, args: list[str] = [], **kwargs
    ) -> list[dict[str, Any]]:
        self._enforce_args(args)
        args = set(args)

        base_query = (
            select(models.Package)
            .join(models.PackageBase)
            .join(
                models.User,
                models.User.ID == models.PackageBase.MaintainerUID,
                isouter=True,
            )
            .where(models.Package.Name.in_(args))
        )

        max_results = config.getint("options", "max_rpc_results")
        query = self.entities(base_query).limit(max_results + 1)
        results = db.get_session().execute(query).all()

        if len(results) > max_results:
            raise RPCError("Too many package results.")

        ids = {pkg.ID for pkg in results}
        self.subquery(ids)

        return self._assemble_json_data(results, self.get_info_json_data)

    def _handle_search_type(
        self, by: str = defaults.RPC_SEARCH_BY, args: list[str] = []
    ) -> list[dict[str, Any]]:
        # If `by` isn't maintainer and we don't have any args, raise an error.
        # In maintainer's case, return all orphans if there are no args,
        # so we need args to pass through to the handler without errors.
        if by != "m" and not len(args):
            raise RPCError("No request type/data specified.")

        arg = args[0] if args else str()
        if by != "m" and len(arg) < 2:
            raise RPCError("Query arg too small.")

        search = RPCSearch()
        search.search_by(by, arg)

        max_results = config.getint("options", "max_rpc_results")

        query = self.entities(search.results()).limit(max_results + 1)

        # For "provides", we need to union our relation search
        # with an exact search since a package always provides itself.
        # Turns out that doing this with an OR statement is extremely slow
        if by == "provides":
            search = RPCSearch()
            search._search_by_exact_name(arg)
            query = query.union(self.entities(search.results()))

        results = query.all()
        if len(results) > max_results:
            raise RPCError("Too many package results.")

        data = self._assemble_json_data(results, self.get_json_data)

        # remove Submitter for search results
        for pkg in data:
            pkg.pop("Submitter")

        return data

    def _handle_msearch_type(
        self, args: list[str] = [], **kwargs
    ) -> list[dict[str, Any]]:
        return self._handle_search_type(by="m", args=args)

    def _handle_suggest_type(self, args: list[str] = [], **kwargs) -> list[str]:
        if not args:
            return []

        arg = args[0]
        return (
            db.get_session()
            .execute(
                select(models.Package.Name)
                .join(models.PackageBase)
                .where(models.Package.Name.like(f"{arg}%"))
                .order_by(models.Package.Name.asc())
                .limit(20)
            )
            .scalars()
            .all()
        )

    def _handle_suggest_pkgbase_type(self, args: list[str] = [], **kwargs) -> list[str]:
        if not args:
            return []

        arg = args[0]
        return (
            db.get_session()
            .execute(
                select(models.PackageBase.Name)
                .where(models.PackageBase.Name.like(f"{arg}%"))
                .order_by(models.PackageBase.Name.asc())
                .limit(20)
            )
            .scalars()
            .all()
        )

    def _is_suggestion(self) -> bool:
        return self.type.startswith("suggest")

    def _handle_callback(
        self, by: str, args: list[str]
    ) -> Union[list[dict[str, Any]], list[str]]:
        # Get a handle to our callback and trap an RPCError with
        # an empty list of results based on callback's execution.
        callback = getattr(self, f"_handle_{self.type.replace('-', '_')}_type")
        results = callback(by=by, args=args)
        return results

    def handle(
        self, by: str = defaults.RPC_SEARCH_BY, args: list[str] = []
    ) -> Union[list[dict[str, Any]], dict[str, Any]]:
        """Request entrypoint. A router should pass v, type and args
        to this function and expect an output dictionary to be returned.

        :param v: RPC version argument
        :param type: RPC type argument
        :param args: Deciphered list of arguments based on arg/arg[] inputs
        """
        # Prepare our output data dictionary with some basic keys.
        data = {"version": self.version, "type": self.type}

        # Run some verification on our given arguments.
        try:
            self._verify_inputs(by=by, args=args)
        except RPCError as exc:
            return self.error(str(exc))

        # Convert by to its aliased value if it has one.
        by = RPC.BY_ALIASES.get(by, by)

        # Process the requested handler.
        try:
            results = self._handle_callback(by, args)
        except RPCError as exc:
            return self.error(str(exc))

        # These types are special: we produce a different kind of
        # successful JSON output: a list of results.
        if self._is_suggestion():
            return results

        # Return JSON output.
        data.update({"resultcount": len(results), "results": results})
        return data
