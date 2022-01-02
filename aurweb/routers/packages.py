from collections import defaultdict
from datetime import datetime
from http import HTTPStatus
from typing import Any, Dict, List

from fastapi import APIRouter, Form, Query, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy import case

import aurweb.filters
import aurweb.packages.util

from aurweb import config, db, defaults, logging, models, util
from aurweb.auth import auth_required, creds
from aurweb.exceptions import InvariantError, ValidationError
from aurweb.models.package_request import ACCEPTED_ID, PENDING_ID, REJECTED_ID
from aurweb.models.relation_type import CONFLICTS_ID, PROVIDES_ID, REPLACES_ID
from aurweb.packages import util as pkgutil
from aurweb.packages import validate
from aurweb.packages.search import PackageSearch
from aurweb.packages.util import get_pkg_or_base, get_pkgreq_by_id
from aurweb.pkgbase import actions as pkgbase_actions
from aurweb.pkgbase import util as pkgbaseutil
from aurweb.scripts import notify
from aurweb.templates import make_context, make_variable_context, render_template

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
    context["PP"] = per_page

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
    limit = config.getint("options", "max_search_results")
    num_packages = search.count(limit)

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

    return render_template(request, "packages.html", context,
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
        models.PackageRelation.RelTypeID == CONFLICTS_ID)
    context["conflicts"] = conflicts

    provides = pkg.package_relations.filter(
        models.PackageRelation.RelTypeID == PROVIDES_ID)
    context["provides"] = provides

    replaces = pkg.package_relations.filter(
        models.PackageRelation.RelTypeID == REPLACES_ID)
    context["replaces"] = replaces

    return render_template(request, "packages/show.html", context)


@router.get("/requests")
@auth_required()
async def requests(request: Request,
                   O: int = Query(default=defaults.O),
                   PP: int = Query(default=defaults.PP)):
    context = make_context(request, "Requests")

    context["q"] = dict(request.query_params)

    O, PP = util.sanitize_params(O, PP)
    context["O"] = O
    context["PP"] = PP

    # A PackageRequest query, with left inner joined User and RequestType.
    query = db.query(models.PackageRequest).join(
        models.User, models.PackageRequest.UsersID == models.User.ID
    ).join(models.RequestType)

    # If the request user is not elevated (TU or Dev), then
    # filter PackageRequests which are owned by the request user.
    if not request.user.is_elevated():
        query = query.filter(models.PackageRequest.UsersID == request.user.ID)

    context["total"] = query.count()
    context["results"] = query.order_by(
        # Order primarily by the Status column being PENDING_ID,
        # and secondarily by RequestTS; both in descending order.
        case([(models.PackageRequest.Status == PENDING_ID, 1)], else_=0).desc(),
        models.PackageRequest.RequestTS.desc()
    ).limit(PP).offset(O).all()

    return render_template(request, "requests.html", context)


@router.get("/pkgbase/{name}/request")
@auth_required()
async def package_request(request: Request, name: str):
    pkgbase = get_pkg_or_base(name, models.PackageBase)
    context = await make_variable_context(request, "Submit Request")
    context["pkgbase"] = pkgbase
    return render_template(request, "pkgbase/request.html", context)


@router.post("/pkgbase/{name}/request")
@auth_required()
async def pkgbase_request_post(request: Request, name: str,
                               type: str = Form(...),
                               merge_into: str = Form(default=None),
                               comments: str = Form(default=str())):
    pkgbase = get_pkg_or_base(name, models.PackageBase)

    # Create our render context.
    context = await make_variable_context(request, "Submit Request")
    context["pkgbase"] = pkgbase
    if type not in {"deletion", "merge", "orphan"}:
        # In the case that someone crafted a POST request with an invalid
        # type, just return them to the request form with BAD_REQUEST status.
        return render_template(request, "pkgbase/request.html", context,
                               status_code=HTTPStatus.BAD_REQUEST)

    try:
        validate.request(pkgbase, type, comments, merge_into, context)
    except ValidationError as exc:
        logger.error(f"Request Validation Error: {str(exc.data)}")
        context["errors"] = exc.data
        return render_template(request, "pkgbase/request.html", context)

    # All good. Create a new PackageRequest based on the given type.
    now = int(datetime.utcnow().timestamp())
    reqtype = db.query(models.RequestType).filter(
        models.RequestType.Name == type).first()
    with db.begin():
        pkgreq = db.create(models.PackageRequest,
                           RequestType=reqtype,
                           User=request.user,
                           RequestTS=now,
                           PackageBase=pkgbase,
                           PackageBaseName=pkgbase.Name,
                           MergeBaseName=merge_into,
                           Comments=comments,
                           ClosureComment=str())

    # Prepare notification object.
    notif = notify.RequestOpenNotification(
        request.user.ID, pkgreq.ID, reqtype.Name,
        pkgreq.PackageBase.ID, merge_into=merge_into or None)

    # Send the notification now that we're out of the DB scope.
    notif.send()

    auto_orphan_age = aurweb.config.getint("options", "auto_orphan_age")
    auto_delete_age = aurweb.config.getint("options", "auto_delete_age")

    ood_ts = pkgbase.OutOfDateTS or 0
    flagged = ood_ts and (now - ood_ts) >= auto_orphan_age
    is_maintainer = pkgbase.Maintainer == request.user
    outdated = (now - pkgbase.SubmittedTS) <= auto_delete_age

    if type == "orphan" and flagged:
        # This request should be auto-accepted.
        with db.begin():
            pkgbase.Maintainer = None
            pkgreq.Status = ACCEPTED_ID
        notif = notify.RequestCloseNotification(
            request.user.ID, pkgreq.ID, pkgreq.status_display())
        notif.send()
        logger.debug(f"New request #{pkgreq.ID} is marked for auto-orphan.")
    elif type == "deletion" and is_maintainer and outdated:
        # This request should be auto-accepted.
        notifs = pkgbase_actions.pkgbase_delete_instance(
            request, pkgbase, comments=comments)
        util.apply_all(notifs, lambda n: n.send())
        logger.debug(f"New request #{pkgreq.ID} is marked for auto-deletion.")

    # Redirect the submitting user to /packages.
    return RedirectResponse("/packages", status_code=HTTPStatus.SEE_OTHER)


@router.get("/requests/{id}/close")
@auth_required()
async def requests_close(request: Request, id: int):
    pkgreq = get_pkgreq_by_id(id)
    if not request.user.is_elevated() and request.user != pkgreq.User:
        # Request user doesn't have permission here: redirect to '/'.
        return RedirectResponse("/", status_code=HTTPStatus.SEE_OTHER)

    context = make_context(request, "Close Request")
    context["pkgreq"] = pkgreq
    return render_template(request, "requests/close.html", context)


@router.post("/requests/{id}/close")
@auth_required()
async def requests_close_post(request: Request, id: int,
                              comments: str = Form(default=str())):
    pkgreq = get_pkgreq_by_id(id)

    # `pkgreq`.User can close their own request.
    approved = [pkgreq.User]
    if not request.user.has_credential(creds.PKGREQ_CLOSE, approved=approved):
        # Request user doesn't have permission here: redirect to '/'.
        return RedirectResponse("/", status_code=HTTPStatus.SEE_OTHER)

    context = make_context(request, "Close Request")
    context["pkgreq"] = pkgreq

    now = int(datetime.utcnow().timestamp())
    with db.begin():
        pkgreq.Closer = request.user
        pkgreq.ClosureComment = comments
        pkgreq.ClosedTS = now
        pkgreq.Status = REJECTED_ID

    notify_ = notify.RequestCloseNotification(
        request.user.ID, pkgreq.ID, pkgreq.status_display())
    notify_.send()

    return RedirectResponse("/requests", status_code=HTTPStatus.SEE_OTHER)


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
@auth_required()
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
