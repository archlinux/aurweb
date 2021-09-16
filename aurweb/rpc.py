import aurweb.config as config

from aurweb import db
from aurweb.models.dependency_type import CHECKDEPENDS_ID, DEPENDS_ID, MAKEDEPENDS_ID, OPTDEPENDS_ID
from aurweb.models.license import License
from aurweb.models.package import Package
from aurweb.models.package_base import PackageBase
from aurweb.models.package_dependency import PackageDependency
from aurweb.models.package_keyword import PackageKeyword
from aurweb.models.package_license import PackageLicense
from aurweb.models.package_relation import PackageRelation
from aurweb.models.package_vote import PackageVote
from aurweb.models.relation_type import CONFLICTS_ID, PROVIDES_ID, REPLACES_ID
from aurweb.models.user import User

# Define dependency types.
DEP_TYPES = {
    DEPENDS_ID: "Depends",
    MAKEDEPENDS_ID: "MakeDepends",
    CHECKDEPENDS_ID: "CheckDepends",
    OPTDEPENDS_ID: "OptDepends"
}

# Define relationship types.
REL_TYPES = {
    CONFLICTS_ID: "Conflicts",
    PROVIDES_ID: "Provides",
    REPLACES_ID: "Replaces"
}


# Define functions for request types.
def add_deps(current_array, db_dep):
    if db_dep.count() > 0:
        # Create lists for all dependency types.
        for i in DEP_TYPES.values():
            current_array[i] = []

        # Generate each dependency item in list.
        for i in db_dep.all():
            dep_string = i.DepName

            # Add relationship version restrictor (i.e. '<=5') if it exists.
            if i.DepCondition is not None:
                dep_string += i.DepCondition

            # Add item to list.
            current_deptype = DEP_TYPES.get(i.DepTypeID)
            current_array[current_deptype] += [dep_string]

        # Remove any dependency lists that are empty.
        for i in DEP_TYPES.values():
            if current_array[i] == []:
                current_array.pop(i)

    return current_array


def add_rels(current_array, db_rel):
    if db_rel.count() > 0:
        # Create lists for all relationship types.
        for i in REL_TYPES.values():
            current_array[i] = []

        # Generate each relationship item in list.
        for i in db_rel.all():
            rel_string = i.RelName

            # Add relationship version restrictor (i.e. '<=5') if it exists.
            if i.RelCondition is not None:
                rel_string += i.RelCondition

            # Add item to list.
            current_reltype = REL_TYPES.get(i.RelTypeID)
            current_array[current_reltype] += [rel_string]

        # Remove any relationship lists that are empty.
        for i in REL_TYPES.values():
            if current_array[i] == []:
                current_array.pop(i)

    return current_array


def run_info(returned_data, package_name, snapshot_uri):
    # Get package name.
    db_package = db.query(Package).filter(Package.Name == package_name)

    if db_package.count() == 0:
        return returned_data

    db_package = db_package.first()

    # Get name of package under PackageBaseID.
    db_package_baseid = db.query(PackageBase).filter(PackageBase.ID == db_package.PackageBaseID).first()

    # Get maintainer info.
    db_package_maintainer = db.query(User).filter(User.ID == db_package_baseid.MaintainerUID).first()

    current_array = {}
    returned_data["resultcount"] = returned_data["resultcount"] + 1

    # Data from the Packages table.
    current_array["ID"] = db_package.ID
    current_array["Name"] = db_package.Name
    current_array["PackageBaseID"] = db_package.PackageBaseID
    current_array["Version"] = db_package.Version
    current_array["Description"] = db_package.Description
    current_array["URL"] = db_package.URL

    # PackageBase table.
    current_array["PackageBase"] = db_package_baseid.Name
    current_array["NumVotes"] = db_package_baseid.NumVotes
    current_array["Popularity"] = db_package_baseid.Popularity
    current_array["OutOfDate"] = db_package_baseid.OutOfDateTS
    current_array["FirstSubmitted"] = db_package_baseid.SubmittedTS
    current_array["LastModified"] = db_package_baseid.ModifiedTS

    # User table.
    try:
        current_array["Maintainer"] = db_package_maintainer.Username
    except AttributeError:
        current_array["Maintainer"] = None

    # Generate and add snapshot_uri.
    current_array["URLPath"] = snapshot_uri.replace("%s", package_name)

    # Add package votes.
    current_array["NumVotes"] = db.query(PackageVote).count()

    # Generate dependency listing.
    db_dep = db.query(PackageDependency).filter(PackageDependency.PackageID == db_package.ID)
    current_array = add_deps(current_array, db_dep)

    # Generate relationship listing.
    db_rel = db.query(PackageRelation).filter(PackageRelation.PackageID == db_package.ID)
    current_array = add_rels(current_array, db_rel)

    # License table.
    current_array["License"] = []

    for i in db.query(PackageLicense).filter(PackageLicense.PackageID == db_package.ID):
        current_array["License"] += [db.query(License).first().Name]

    # Keywords table.
    current_array["Keywords"] = []

    for i in db.query(PackageKeyword).filter(PackageKeyword.PackageBaseID == db_package_baseid.ID):
        current_array["Keywords"] += [i.Keyword]

    # Add current array to returned results.
    returned_data["results"] += [current_array]
    return returned_data


def RPC(**function_args):
    # Get arguments.
    #
    # We'll use 'v' in the future when we add v6.
    # v = function_args.get("v")
    type = function_args.get("type")
    args = function_args.get("argument_list")
    returned_data = function_args.get("returned_data")

    # Get Snapshot URI
    snapshot_uri = config.get("options", "snapshot_uri")

    # Set request type to run.
    type_actions = {
        "info": run_info,
        "multiinfo": run_info
    }

    # This if statement should always be executed, as we checked if the
    # specified type was valid in aurweb/routers/rpc.py.
    if type in type_actions:
        run_request = type_actions.get(type)

        # If type is 'info', overwrite type to 'multiinfo' to match the
        # behavior of the PHP implementation.
        if type == "info":
            returned_data["type"] = "multiinfo"

        # Remove duplicate arguments if type is 'multiinfo' so we don't
        # fetch results for a package multiple times.
        if returned_data["type"] == "multiinfo":
            args = set(args)

        for i in args:
            returned_data = run_request(returned_data, i, snapshot_uri)

    elif type is None:
        returned_data["type"] = "error"
        returned_data["error"] = "No request type/data specified."

    else:
        returned_data["type"] = "error"
        returned_data["error"] = "Incorrect request type specified."


    return returned_data
