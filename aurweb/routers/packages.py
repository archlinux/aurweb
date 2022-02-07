from collections import defaultdict
from http import HTTPStatus
from typing import Any, Dict, List

from fastapi import APIRouter, Form, Request, Response

import aurweb.filters  # noqa: F401

from aurweb import config, db, defaults, logging, models, util
from aurweb.auth import creds, requires_auth
from aurweb.exceptions import InvariantError
from aurweb.models.relation_type import CONFLICTS_ID, PROVIDES_ID, REPLACES_ID
from aurweb.packages import util as pkgutil
from aurweb.packages.search import PackageSearch
from aurweb.packages.util import get_pkg_or_base
from aurweb.pkgbase import actions as pkgbase_actions
from aurweb.pkgbase import util as pkgbaseutil
from aurweb.templates import make_context, render_template

logger = logging.get_logger(__name__)
router = APIRouter()


async def packages_get(request: Request, context: Dict[str, Any],
                       status_code: HTTPStatus = HTTPStatus.OK):
    # Query parameters used in this request.
    context["q"] = dict(request.query_params)

    # Per page and offset.
    offset, per_page = util.sanitize_params(
        request.query_params.get("O", defaults.O),
        request.query_params.get("PP", defaults.PP))
    context["O"] = offset

    # Limit PP to options.max_search_results
    max_search_results = aurweb.config.getint("options", "max_search_results")
    context["PP"] = per_page = min(per_page, max_search_results)

    # Query search by.
    search_by = context["SeB"] = request.query_params.get("SeB", "nd")

    # Query sort by.
    sort_by = context["SB"] = request.query_params.get("SB", "p")

    # Query sort order.
    sort_order = request.query_params.get("SO", None)

    # Apply ordering, limit and offset.
    search = PackageSearch(request.user)

    # For each keyword found in K, apply a search_by filter.
    # This means that for any sentences separated by spaces,
    # they are used as if they were ANDed.
    keywords = context["K"] = request.query_params.get("K", str())
    keywords = keywords.split(" ")
    for keyword in keywords:
        search.search_by(search_by, keyword)

    # Collect search result count here; we've applied our keywords.
    # Including more query operations below, like ordering, will
    # increase the amount of time required to collect a count.
    num_packages = search.count()

    flagged = request.query_params.get("outdated", None)
    if flagged:
        # If outdated was given, set it up in the context.
        context["outdated"] = flagged

        # When outdated is set to "on," we filter records which do have
        # an OutOfDateTS. When it's set to "off," we filter out any which
        # do **not** have OutOfDateTS.
        criteria = None
        if flagged == "on":
            criteria = models.PackageBase.OutOfDateTS.isnot
        else:
            criteria = models.PackageBase.OutOfDateTS.is_

        # Apply the flag criteria to our PackageSearch.query.
        search.query = search.query.filter(criteria(None))

    submit = request.query_params.get("submit", "Go")
    if submit == "Orphans":
        # If the user clicked the "Orphans" button, we only want
        # orphaned packages.
        search.query = search.query.filter(
            models.PackageBase.MaintainerUID.is_(None))

    # Apply user-specified specified sort column and ordering.
    search.sort_by(sort_by, sort_order)

    # If no SO was given, default the context SO to 'a' (Ascending).
    # By default, if no SO is given, the search should sort by 'd'
    # (Descending), but display "Ascending" for the Sort order select.
    if sort_order is None:
        sort_order = "a"
    context["SO"] = sort_order

    # Insert search results into the context.
    results = search.results().with_entities(
        models.Package.ID,
        models.Package.Name,
        models.Package.PackageBaseID,
        models.Package.Version,
        models.Package.Description,
        models.PackageBase.Popularity,
        models.PackageBase.NumVotes,
        models.PackageBase.OutOfDateTS,
        models.User.Username.label("Maintainer"),
        models.PackageVote.PackageBaseID.label("Voted"),
        models.PackageNotification.PackageBaseID.label("Notify")
    )

    packages = results.limit(per_page).offset(offset)
    context["packages"] = packages
    context["packages_count"] = num_packages

    return render_template(request, "packages/index.html", context,
                           status_code=status_code)


@router.get("/packages")
async def packages(request: Request) -> Response:
    context = make_context(request, "Packages")
    return await packages_get(request, context)


@router.get("/packages/{name}")
async def package(request: Request, name: str) -> Response:
    # Get the Package.
    pkg = get_pkg_or_base(name, models.Package)
    pkgbase = pkg.PackageBase

    rels = pkg.package_relations.order_by(models.PackageRelation.RelName.asc())
    rels_data = defaultdict(list)
    for rel in rels:
        if rel.RelTypeID == CONFLICTS_ID:
            rels_data["c"].append(rel)
        elif rel.RelTypeID == PROVIDES_ID:
            rels_data["p"].append(rel)
        elif rel.RelTypeID == REPLACES_ID:
            rels_data["r"].append(rel)

    # Add our base information.
    context = pkgbaseutil.make_context(request, pkgbase)
    context["package"] = pkg

    # Package sources.
    context["sources"] = pkg.package_sources.order_by(
        models.PackageSource.Source.asc()).all()

    # Package dependencies.
    max_depends = config.getint("options", "max_depends")
    context["dependencies"] = pkg.package_dependencies.order_by(
        models.PackageDependency.DepTypeID.asc(),
        models.PackageDependency.DepName.asc()
    ).limit(max_depends).all()

    # Package requirements (other packages depend on this one).
    context["required_by"] = pkgutil.pkg_required(
        pkg.Name, [p.RelName for p in rels_data.get("p", [])], max_depends)

    context["licenses"] = pkg.package_licenses

    conflicts = pkg.package_relations.filter(
        models.PackageRelation.RelTypeID == CONFLICTS_ID
    ).order_by(models.PackageRelation.RelName.asc())
    context["conflicts"] = conflicts

    provides = pkg.package_relations.filter(
        models.PackageRelation.RelTypeID == PROVIDES_ID
    ).order_by(models.PackageRelation.RelName.asc())
    context["provides"] = provides

    replaces = pkg.package_relations.filter(
        models.PackageRelation.RelTypeID == REPLACES_ID
    ).order_by(models.PackageRelation.RelName.asc())
    context["replaces"] = replaces

    return render_template(request, "packages/show.html", context)


async def packages_unflag(request: Request, package_ids: List[int] = [],
                          **kwargs):
    if not package_ids:
        return (False, ["You did not select any packages to unflag."])

    # Holds the set of package bases we're looking to unflag.
    # Constructed below via looping through the packages query.
    bases = set()

    package_ids = set(package_ids)  # Convert this to a set for O(1).
    packages = db.query(models.Package).filter(
        models.Package.ID.in_(package_ids)).all()
    for pkg in packages:
        has_cred = request.user.has_credential(
            creds.PKGBASE_UNFLAG, approved=[pkg.PackageBase.Flagger])
        if not has_cred:
            return (False, ["You did not select any packages to unflag."])

        if pkg.PackageBase not in bases:
            bases.update({pkg.PackageBase})

    for pkgbase in bases:
        pkgbase_actions.pkgbase_unflag_instance(request, pkgbase)
    return (True, ["The selected packages have been unflagged."])


async def packages_notify(request: Request, package_ids: List[int] = [],
                          **kwargs):
    # In cases where we encounter errors with the request, we'll
    # use this error tuple as a return value.
    # TODO: This error does not yet have a translation.
    error_tuple = (False,
                   ["You did not select any packages to be notified about."])
    if not package_ids:
        return error_tuple

    bases = set()
    package_ids = set(package_ids)
    packages = db.query(models.Package).filter(
        models.Package.ID.in_(package_ids)).all()

    for pkg in packages:
        if pkg.PackageBase not in bases:
            bases.update({pkg.PackageBase})

    # Perform some checks on what the user selected for notify.
    for pkgbase in bases:
        notif = db.query(pkgbase.notifications.filter(
            models.PackageNotification.UserID == request.user.ID
        ).exists()).scalar()
        has_cred = request.user.has_credential(creds.PKGBASE_NOTIFY)

        # If the request user either does not have credentials
        # or the notification already exists:
        if not (has_cred and not notif):
            return error_tuple

    # If we get here, user input is good.
    for pkgbase in bases:
        pkgbase_actions.pkgbase_notify_instance(request, pkgbase)

    # TODO: This message does not yet have a translation.
    return (True, ["The selected packages' notifications have been enabled."])


async def packages_unnotify(request: Request, package_ids: List[int] = [],
                            **kwargs):
    if not package_ids:
        # TODO: This error does not yet have a translation.
        return (False,
                ["You did not select any packages for notification removal."])

    # TODO: This error does not yet have a translation.
    error_tuple = (
        False,
        ["A package you selected does not have notifications enabled."]
    )

    bases = set()
    package_ids = set(package_ids)
    packages = db.query(models.Package).filter(
        models.Package.ID.in_(package_ids)).all()

    for pkg in packages:
        if pkg.PackageBase not in bases:
            bases.update({pkg.PackageBase})

    # Perform some checks on what the user selected for notify.
    for pkgbase in bases:
        notif = db.query(pkgbase.notifications.filter(
            models.PackageNotification.UserID == request.user.ID
        ).exists()).scalar()
        if not notif:
            return error_tuple

    for pkgbase in bases:
        pkgbase_actions.pkgbase_unnotify_instance(request, pkgbase)

    # TODO: This message does not yet have a translation.
    return (True, ["The selected packages' notifications have been removed."])


async def packages_adopt(request: Request, package_ids: List[int] = [],
                         confirm: bool = False, **kwargs):
    if not package_ids:
        return (False, ["You did not select any packages to adopt."])

    if not confirm:
        return (False, ["The selected packages have not been adopted, "
                        "check the confirmation checkbox."])

    bases = set()
    package_ids = set(package_ids)
    packages = db.query(models.Package).filter(
        models.Package.ID.in_(package_ids)).all()

    for pkg in packages:
        if pkg.PackageBase not in bases:
            bases.update({pkg.PackageBase})

    # Check that the user has credentials for every package they selected.
    for pkgbase in bases:
        has_cred = request.user.has_credential(creds.PKGBASE_ADOPT)
        if not (has_cred or not pkgbase.Maintainer):
            # TODO: This error needs to be translated.
            return (False, ["You are not allowed to adopt one of the "
                            "packages you selected."])

    # Now, really adopt the bases.
    for pkgbase in bases:
        pkgbase_actions.pkgbase_adopt_instance(request, pkgbase)

    return (True, ["The selected packages have been adopted."])


def disown_all(request: Request, pkgbases: List[models.PackageBase]) \
        -> List[str]:
    errors = []
    for pkgbase in pkgbases:
        try:
            pkgbase_actions.pkgbase_disown_instance(request, pkgbase)
        except InvariantError as exc:
            errors.append(str(exc))
    return errors


async def packages_disown(request: Request, package_ids: List[int] = [],
                          confirm: bool = False, **kwargs):
    if not package_ids:
        return (False, ["You did not select any packages to disown."])

    if not confirm:
        return (False, ["The selected packages have not been disowned, "
                        "check the confirmation checkbox."])

    bases = set()
    package_ids = set(package_ids)
    packages = db.query(models.Package).filter(
        models.Package.ID.in_(package_ids)).all()

    for pkg in packages:
        if pkg.PackageBase not in bases:
            bases.update({pkg.PackageBase})

    # Check that the user has credentials for every package they selected.
    for pkgbase in bases:
        has_cred = request.user.has_credential(creds.PKGBASE_DISOWN,
                                               approved=[pkgbase.Maintainer])
        if not has_cred:
            # TODO: This error needs to be translated.
            return (False, ["You are not allowed to disown one "
                            "of the packages you selected."])

    # Now, disown all the bases if we can.
    if errors := disown_all(request, bases):
        return (False, errors)

    return (True, ["The selected packages have been disowned."])


async def packages_delete(request: Request, package_ids: List[int] = [],
                          confirm: bool = False, merge_into: str = str(),
                          **kwargs):
    if not package_ids:
        return (False, ["You did not select any packages to delete."])

    if not confirm:
        return (False, ["The selected packages have not been deleted, "
                        "check the confirmation checkbox."])

    if not request.user.has_credential(creds.PKGBASE_DELETE):
        return (False, ["You do not have permission to delete packages."])

    # set-ify package_ids and query the database for related records.
    package_ids = set(package_ids)
    packages = db.query(models.Package).filter(
        models.Package.ID.in_(package_ids)).all()

    if len(packages) != len(package_ids):
        # Let the user know there was an issue with their input: they have
        # provided at least one package_id which does not exist in the DB.
        # TODO: This error has not yet been translated.
        return (False, ["One of the packages you selected does not exist."])

    # Make a set out of all package bases related to `packages`.
    bases = {pkg.PackageBase for pkg in packages}
    deleted_bases, notifs = [], []
    for pkgbase in bases:
        deleted_bases.append(pkgbase.Name)
        notifs += pkgbase_actions.pkgbase_delete_instance(request, pkgbase)

    # Log out the fact that this happened for accountability.
    logger.info(f"Privileged user '{request.user.Username}' deleted the "
                f"following package bases: {str(deleted_bases)}.")

    util.apply_all(notifs, lambda n: n.send())
    return (True, ["The selected packages have been deleted."])

# A mapping of action string -> callback functions used within the
# `packages_post` route below. We expect any action callback to
# return a tuple in the format: (succeeded: bool, message: List[str]).
PACKAGE_ACTIONS = {
    "unflag": packages_unflag,
    "notify": packages_notify,
    "unnotify": packages_unnotify,
    "adopt": packages_adopt,
    "disown": packages_disown,
    "delete": packages_delete,
}


@router.post("/packages")
@requires_auth
async def packages_post(request: Request,
                        IDs: List[int] = Form(default=[]),
                        action: str = Form(default=str()),
                        confirm: bool = Form(default=False)):

    # If an invalid action is specified, just render GET /packages
    # with an BAD_REQUEST status_code.
    if action not in PACKAGE_ACTIONS:
        context = make_context(request, "Packages")
        return await packages_get(request, context, HTTPStatus.BAD_REQUEST)

    context = make_context(request, "Packages")

    # We deal with `IDs`, `merge_into` and `confirm` arguments
    # within action callbacks.
    callback = PACKAGE_ACTIONS.get(action)
    retval = await callback(request, package_ids=IDs, confirm=confirm)
    if retval:  # If *anything* was returned:
        success, messages = retval
        if not success:
            # If the first element was False:
            context["errors"] = messages
            return await packages_get(request, context, HTTPStatus.BAD_REQUEST)
        else:
            # Otherwise:
            context["success"] = messages

    return await packages_get(request, context)
