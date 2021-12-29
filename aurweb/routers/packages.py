from collections import defaultdict
from datetime import datetime
from http import HTTPStatus
from typing import Any, Dict, List

from fastapi import APIRouter, Form, HTTPException, Query, Request, Response
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy import and_, case

import aurweb.filters
import aurweb.packages.util

from aurweb import config, db, defaults, l10n, logging, models, util
from aurweb.auth import auth_required, creds
from aurweb.exceptions import InvariantError, ValidationError
from aurweb.models.package_request import ACCEPTED_ID, PENDING_ID, REJECTED_ID
from aurweb.models.relation_type import CONFLICTS_ID, PROVIDES_ID, REPLACES_ID
from aurweb.models.request_type import DELETION_ID, MERGE_ID, ORPHAN_ID
from aurweb.packages import util as pkgutil
from aurweb.packages import validate
from aurweb.packages.requests import handle_request, update_closure_comment
from aurweb.packages.search import PackageSearch
from aurweb.packages.util import get_pkg_or_base, get_pkgbase_comment, get_pkgreq_by_id
from aurweb.scripts import notify, popupdate
from aurweb.scripts.rendercomment import update_comment_render_fastapi
from aurweb.templates import make_context, make_variable_context, render_raw_template, render_template

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


def delete_package(request: Request, package: models.Package,
                   merge_into: models.PackageBase = None,
                   comments: str = str()):
    bases_to_delete = []

    target = db.query(models.PackageBase).filter(
        models.PackageBase.Name == merge_into
    ).first()

    notifs = []
    # In all cases, though, just delete the Package in question.
    if package.PackageBase.packages.count() == 1:
        notifs = handle_request(request, DELETION_ID, package.PackageBase,
                                target=target)

        bases_to_delete.append(package.PackageBase)

        with db.begin():
            update_closure_comment(package.PackageBase, DELETION_ID, comments,
                                   target=target)

        # Prepare DeleteNotification.
        notifs.append(
            notify.DeleteNotification(request.user.ID, package.PackageBase.ID)
        )

    # Perform all the deletions.
    with db.begin():
        db.delete(package)
        db.delete_all(bases_to_delete)

    # Send out all the notifications.
    util.apply_all(notifs, lambda n: n.send())


async def make_single_context(request: Request,
                              pkgbase: models.PackageBase) -> Dict[str, Any]:
    """ Make a basic context for package or pkgbase.

    :param request: FastAPI request
    :param pkgbase: PackageBase instance
    :return: A pkgbase context without specific differences
    """
    context = make_context(request, pkgbase.Name)
    context["git_clone_uri_anon"] = aurweb.config.get("options",
                                                      "git_clone_uri_anon")
    context["git_clone_uri_priv"] = aurweb.config.get("options",
                                                      "git_clone_uri_priv")
    context["pkgbase"] = pkgbase
    context["packages_count"] = pkgbase.packages.count()
    context["keywords"] = pkgbase.keywords
    context["comments"] = pkgbase.comments.order_by(
        models.PackageComment.CommentTS.desc()
    )
    context["pinned_comments"] = pkgbase.comments.filter(
        models.PackageComment.PinnedTS != 0
    ).order_by(models.PackageComment.CommentTS.desc())

    context["is_maintainer"] = (request.user.is_authenticated()
                                and request.user.ID == pkgbase.MaintainerUID)
    context["notified"] = request.user.notified(pkgbase)

    context["out_of_date"] = bool(pkgbase.OutOfDateTS)

    context["voted"] = request.user.package_votes.filter(
        models.PackageVote.PackageBaseID == pkgbase.ID).scalar()

    context["requests"] = pkgbase.requests.filter(
        models.PackageRequest.ClosedTS.is_(None)
    ).count()

    return context


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
    context = await make_single_context(request, pkgbase)
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


@router.get("/pkgbase/{name}")
async def package_base(request: Request, name: str) -> Response:
    # Get the PackageBase.
    pkgbase = get_pkg_or_base(name, models.PackageBase)

    # If this is not a split package, redirect to /packages/{name}.
    if pkgbase.packages.count() == 1:
        return RedirectResponse(f"/packages/{name}",
                                status_code=int(HTTPStatus.SEE_OTHER))

    # Add our base information.
    context = await make_single_context(request, pkgbase)
    context["packages"] = pkgbase.packages.all()

    return render_template(request, "pkgbase.html", context)


@router.get("/pkgbase/{name}/voters")
async def package_base_voters(request: Request, name: str) -> Response:
    # Get the PackageBase.
    pkgbase = get_pkg_or_base(name, models.PackageBase)

    if not request.user.has_credential(creds.PKGBASE_LIST_VOTERS):
        return RedirectResponse(f"/pkgbase/{name}",
                                status_code=HTTPStatus.SEE_OTHER)

    context = make_context(request, "Voters")
    context["pkgbase"] = pkgbase
    return render_template(request, "pkgbase/voters.html", context)


@router.post("/pkgbase/{name}/comments")
@auth_required()
async def pkgbase_comments_post(
        request: Request, name: str,
        comment: str = Form(default=str()),
        enable_notifications: bool = Form(default=False)):
    """ Add a new comment. """
    pkgbase = get_pkg_or_base(name, models.PackageBase)

    if not comment:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST)

    # If the provided comment is different than the record's version,
    # update the db record.
    now = int(datetime.utcnow().timestamp())
    with db.begin():
        comment = db.create(models.PackageComment, User=request.user,
                            PackageBase=pkgbase,
                            Comments=comment, RenderedComment=str(),
                            CommentTS=now)

        if enable_notifications and not request.user.notified(pkgbase):
            db.create(models.PackageNotification,
                      User=request.user,
                      PackageBase=pkgbase)
    update_comment_render_fastapi(comment)

    # Redirect to the pkgbase page.
    return RedirectResponse(f"/pkgbase/{pkgbase.Name}#comment-{comment.ID}",
                            status_code=HTTPStatus.SEE_OTHER)


@router.get("/pkgbase/{name}/comments/{id}/form")
@auth_required()
async def pkgbase_comment_form(request: Request, name: str, id: int,
                               next: str = Query(default=None)):
    """ Produce a comment form for comment {id}. """
    pkgbase = get_pkg_or_base(name, models.PackageBase)
    comment = pkgbase.comments.filter(models.PackageComment.ID == id).first()
    if not comment:
        return JSONResponse({}, status_code=HTTPStatus.NOT_FOUND)

    if not request.user.is_elevated() and request.user != comment.User:
        return JSONResponse({}, status_code=HTTPStatus.UNAUTHORIZED)

    context = await make_single_context(request, pkgbase)
    context["comment"] = comment

    if not next:
        next = f"/pkgbase/{name}"

    context["next"] = next

    form = render_raw_template(
        request, "partials/packages/comment_form.html", context)
    return JSONResponse({"form": form})


@router.post("/pkgbase/{name}/comments/{id}")
@auth_required()
async def pkgbase_comment_post(
        request: Request, name: str, id: int,
        comment: str = Form(default=str()),
        enable_notifications: bool = Form(default=False),
        next: str = Form(default=None)):
    pkgbase = get_pkg_or_base(name, models.PackageBase)
    db_comment = get_pkgbase_comment(pkgbase, id)

    if not comment:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST)

    # If the provided comment is different than the record's version,
    # update the db record.
    now = int(datetime.utcnow().timestamp())
    if db_comment.Comments != comment:
        with db.begin():
            db_comment.Comments = comment
            db_comment.Editor = request.user
            db_comment.EditedTS = now

            db_notif = request.user.notifications.filter(
                models.PackageNotification.PackageBaseID == pkgbase.ID
            ).first()
            if enable_notifications and not db_notif:
                db.create(models.PackageNotification,
                          User=request.user,
                          PackageBase=pkgbase)
    update_comment_render_fastapi(db_comment)

    if not next:
        next = f"/pkgbase/{pkgbase.Name}"

    # Redirect to the pkgbase page anchored to the updated comment.
    return RedirectResponse(f"{next}#comment-{db_comment.ID}",
                            status_code=HTTPStatus.SEE_OTHER)


@router.get("/pkgbase/{name}/comments/{id}/edit")
@auth_required()
async def pkgbase_comment_edit(request: Request, name: str, id: int,
                               next: str = Form(default=None)):
    pkgbase = get_pkg_or_base(name, models.PackageBase)
    comment = get_pkgbase_comment(pkgbase, id)

    if not next:
        next = f"/pkgbase/{name}"

    context = await make_variable_context(request, "Edit comment", next=next)
    context["comment"] = comment
    return render_template(request, "packages/comments/edit.html", context)


@router.post("/pkgbase/{name}/comments/{id}/delete")
@auth_required()
async def pkgbase_comment_delete(request: Request, name: str, id: int,
                                 next: str = Form(default=None)):
    pkgbase = get_pkg_or_base(name, models.PackageBase)
    comment = get_pkgbase_comment(pkgbase, id)

    authorized = request.user.has_credential(creds.COMMENT_DELETE,
                                             [comment.User])
    if not authorized:
        _ = l10n.get_translator_for_request(request)
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail=_("You are not allowed to delete this comment."))

    now = int(datetime.utcnow().timestamp())
    with db.begin():
        comment.Deleter = request.user
        comment.DelTS = now

    if not next:
        next = f"/pkgbase/{name}"

    return RedirectResponse(next, status_code=HTTPStatus.SEE_OTHER)


@router.post("/pkgbase/{name}/comments/{id}/undelete")
@auth_required()
async def pkgbase_comment_undelete(request: Request, name: str, id: int,
                                   next: str = Form(default=None)):
    pkgbase = get_pkg_or_base(name, models.PackageBase)
    comment = get_pkgbase_comment(pkgbase, id)

    has_cred = request.user.has_credential(creds.COMMENT_UNDELETE,
                                           approved=[comment.User])
    if not has_cred:
        _ = l10n.get_translator_for_request(request)
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail=_("You are not allowed to undelete this comment."))

    with db.begin():
        comment.Deleter = None
        comment.DelTS = None

    if not next:
        next = f"/pkgbase/{name}"

    return RedirectResponse(next, status_code=HTTPStatus.SEE_OTHER)


@router.post("/pkgbase/{name}/comments/{id}/pin")
@auth_required()
async def pkgbase_comment_pin(request: Request, name: str, id: int,
                              next: str = Form(default=None)):
    pkgbase = get_pkg_or_base(name, models.PackageBase)
    comment = get_pkgbase_comment(pkgbase, id)

    has_cred = request.user.has_credential(creds.COMMENT_PIN,
                                           approved=[pkgbase.Maintainer])
    if not has_cred:
        _ = l10n.get_translator_for_request(request)
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail=_("You are not allowed to pin this comment."))

    now = int(datetime.utcnow().timestamp())
    with db.begin():
        comment.PinnedTS = now

    if not next:
        next = f"/pkgbase/{name}"

    return RedirectResponse(next, status_code=HTTPStatus.SEE_OTHER)


@router.post("/pkgbase/{name}/comments/{id}/unpin")
@auth_required()
async def pkgbase_comment_unpin(request: Request, name: str, id: int,
                                next: str = Form(default=None)):
    pkgbase = get_pkg_or_base(name, models.PackageBase)
    comment = get_pkgbase_comment(pkgbase, id)

    has_cred = request.user.has_credential(creds.COMMENT_PIN,
                                           approved=[pkgbase.Maintainer])
    if not has_cred:
        _ = l10n.get_translator_for_request(request)
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail=_("You are not allowed to unpin this comment."))

    with db.begin():
        comment.PinnedTS = 0

    if not next:
        next = f"/pkgbase/{name}"

    return RedirectResponse(next, status_code=HTTPStatus.SEE_OTHER)


@router.get("/pkgbase/{name}/comaintainers")
@auth_required()
async def package_base_comaintainers(request: Request, name: str) -> Response:
    # Get the PackageBase.
    pkgbase = get_pkg_or_base(name, models.PackageBase)

    # Unauthorized users (Non-TU/Dev and not the pkgbase maintainer)
    # get redirected to the package base's page.
    has_creds = request.user.has_credential(creds.PKGBASE_EDIT_COMAINTAINERS,
                                            approved=[pkgbase.Maintainer])
    if not has_creds:
        return RedirectResponse(f"/pkgbase/{name}",
                                status_code=HTTPStatus.SEE_OTHER)

    # Add our base information.
    context = make_context(request, "Manage Co-maintainers")
    context["pkgbase"] = pkgbase

    context["comaintainers"] = [
        c.User.Username for c in pkgbase.comaintainers
    ]

    return render_template(request, "pkgbase/comaintainers.html", context)


@router.post("/pkgbase/{name}/comaintainers")
@auth_required()
async def package_base_comaintainers_post(
        request: Request, name: str,
        users: str = Form(default=str())) -> Response:
    # Get the PackageBase.
    pkgbase = get_pkg_or_base(name, models.PackageBase)

    # Unauthorized users (Non-TU/Dev and not the pkgbase maintainer)
    # get redirected to the package base's page.
    has_creds = request.user.has_credential(creds.PKGBASE_EDIT_COMAINTAINERS,
                                            approved=[pkgbase.Maintainer])
    if not has_creds:
        return RedirectResponse(f"/pkgbase/{name}",
                                status_code=HTTPStatus.SEE_OTHER)

    users = {e.strip() for e in users.split("\n") if bool(e.strip())}
    records = {c.User.Username for c in pkgbase.comaintainers}

    users_to_rm = records.difference(users)
    pkgutil.remove_comaintainers(pkgbase, users_to_rm)
    logger.debug(f"{request.user} removed comaintainers from "
                 f"{pkgbase.Name}: {users_to_rm}")

    users_to_add = users.difference(records)
    error = pkgutil.add_comaintainers(request, pkgbase, users_to_add)
    if error:
        context = make_context(request, "Manage Co-maintainers")
        context["pkgbase"] = pkgbase
        context["comaintainers"] = [
            c.User.Username for c in pkgbase.comaintainers
        ]
        context["errors"] = [error]
        return render_template(request, "pkgbase/comaintainers.html", context)

    logger.debug(f"{request.user} added comaintainers to "
                 f"{pkgbase.Name}: {users_to_add}")

    return RedirectResponse(f"/pkgbase/{pkgbase.Name}",
                            status_code=HTTPStatus.SEE_OTHER)


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
        packages = pkgbase.packages.all()
        for package in packages:
            delete_package(request, package)
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


@router.post("/pkgbase/{name}/keywords")
async def pkgbase_keywords(request: Request, name: str,
                           keywords: str = Form(default=str())):
    pkgbase = get_pkg_or_base(name, models.PackageBase)
    keywords = set(keywords.split(" "))

    # Delete all keywords which are not supplied by the user.
    other_keywords = pkgbase.keywords.filter(
        ~models.PackageKeyword.Keyword.in_(keywords))
    other_keyword_strings = [kwd.Keyword for kwd in other_keywords]

    existing_keywords = set(
        kwd.Keyword for kwd in
        pkgbase.keywords.filter(
            ~models.PackageKeyword.Keyword.in_(other_keyword_strings))
    )
    with db.begin():
        db.delete_all(other_keywords)
        for keyword in keywords.difference(existing_keywords):
            db.create(models.PackageKeyword,
                      PackageBase=pkgbase,
                      Keyword=keyword)

    return RedirectResponse(f"/pkgbase/{name}",
                            status_code=HTTPStatus.SEE_OTHER)


@router.get("/pkgbase/{name}/flag")
@auth_required()
async def pkgbase_flag_get(request: Request, name: str):
    pkgbase = get_pkg_or_base(name, models.PackageBase)

    has_cred = request.user.has_credential(creds.PKGBASE_FLAG)
    if not has_cred or pkgbase.Flagger is not None:
        return RedirectResponse(f"/pkgbase/{name}",
                                status_code=HTTPStatus.SEE_OTHER)

    context = make_context(request, "Flag Package Out-Of-Date")
    context["pkgbase"] = pkgbase
    return render_template(request, "packages/flag.html", context)


@router.post("/pkgbase/{name}/flag")
@auth_required()
async def pkgbase_flag_post(request: Request, name: str,
                            comments: str = Form(default=str())):
    pkgbase = get_pkg_or_base(name, models.PackageBase)

    if not comments:
        context = make_context(request, "Flag Package Out-Of-Date")
        context["pkgbase"] = pkgbase
        context["errors"] = ["The selected packages have not been flagged, "
                             "please enter a comment."]
        return render_template(request, "packages/flag.html", context,
                               status_code=HTTPStatus.BAD_REQUEST)

    has_cred = request.user.has_credential(creds.PKGBASE_FLAG)
    if has_cred and not pkgbase.Flagger:
        now = int(datetime.utcnow().timestamp())
        with db.begin():
            pkgbase.OutOfDateTS = now
            pkgbase.Flagger = request.user
            pkgbase.FlaggerComment = comments

    return RedirectResponse(f"/pkgbase/{name}",
                            status_code=HTTPStatus.SEE_OTHER)


@router.get("/pkgbase/{name}/flag-comment")
async def pkgbase_flag_comment(request: Request, name: str):
    pkgbase = get_pkg_or_base(name, models.PackageBase)

    if pkgbase.Flagger is None:
        return RedirectResponse(f"/pkgbase/{name}",
                                status_code=HTTPStatus.SEE_OTHER)

    context = make_context(request, "Flag Comment")
    context["pkgbase"] = pkgbase
    return render_template(request, "packages/flag-comment.html", context)


def pkgbase_unflag_instance(request: Request, pkgbase: models.PackageBase):
    has_cred = request.user.has_credential(
        creds.PKGBASE_UNFLAG, approved=[pkgbase.Flagger, pkgbase.Maintainer])
    if has_cred:
        with db.begin():
            pkgbase.OutOfDateTS = None
            pkgbase.Flagger = None
            pkgbase.FlaggerComment = str()


@router.post("/pkgbase/{name}/unflag")
@auth_required()
async def pkgbase_unflag(request: Request, name: str):
    pkgbase = get_pkg_or_base(name, models.PackageBase)
    pkgbase_unflag_instance(request, pkgbase)
    return RedirectResponse(f"/pkgbase/{name}",
                            status_code=HTTPStatus.SEE_OTHER)


def pkgbase_notify_instance(request: Request, pkgbase: models.PackageBase):
    notif = db.query(pkgbase.notifications.filter(
        models.PackageNotification.UserID == request.user.ID
    ).exists()).scalar()
    has_cred = request.user.has_credential(creds.PKGBASE_NOTIFY)
    if has_cred and not notif:
        with db.begin():
            db.create(models.PackageNotification,
                      PackageBase=pkgbase,
                      User=request.user)


@router.post("/pkgbase/{name}/notify")
@auth_required()
async def pkgbase_notify(request: Request, name: str):
    pkgbase = get_pkg_or_base(name, models.PackageBase)
    pkgbase_notify_instance(request, pkgbase)
    return RedirectResponse(f"/pkgbase/{name}",
                            status_code=HTTPStatus.SEE_OTHER)


def pkgbase_unnotify_instance(request: Request, pkgbase: models.PackageBase):
    notif = pkgbase.notifications.filter(
        models.PackageNotification.UserID == request.user.ID
    ).first()
    has_cred = request.user.has_credential(creds.PKGBASE_NOTIFY)
    if has_cred and notif:
        with db.begin():
            db.delete(notif)


@router.post("/pkgbase/{name}/unnotify")
@auth_required()
async def pkgbase_unnotify(request: Request, name: str):
    pkgbase = get_pkg_or_base(name, models.PackageBase)
    pkgbase_unnotify_instance(request, pkgbase)
    return RedirectResponse(f"/pkgbase/{name}",
                            status_code=HTTPStatus.SEE_OTHER)


@router.post("/pkgbase/{name}/vote")
@auth_required()
async def pkgbase_vote(request: Request, name: str):
    pkgbase = get_pkg_or_base(name, models.PackageBase)

    vote = pkgbase.package_votes.filter(
        models.PackageVote.UsersID == request.user.ID
    ).first()
    has_cred = request.user.has_credential(creds.PKGBASE_VOTE)
    if has_cred and not vote:
        now = int(datetime.utcnow().timestamp())
        with db.begin():
            db.create(models.PackageVote,
                      User=request.user,
                      PackageBase=pkgbase,
                      VoteTS=now)

        # Update NumVotes/Popularity.
        popupdate.run_single(pkgbase)

    return RedirectResponse(f"/pkgbase/{name}",
                            status_code=HTTPStatus.SEE_OTHER)


@router.post("/pkgbase/{name}/unvote")
@auth_required()
async def pkgbase_unvote(request: Request, name: str):
    pkgbase = get_pkg_or_base(name, models.PackageBase)

    vote = pkgbase.package_votes.filter(
        models.PackageVote.UsersID == request.user.ID
    ).first()
    has_cred = request.user.has_credential(creds.PKGBASE_VOTE)
    if has_cred and vote:
        with db.begin():
            db.delete(vote)

        # Update NumVotes/Popularity.
        popupdate.run_single(pkgbase)

    return RedirectResponse(f"/pkgbase/{name}",
                            status_code=HTTPStatus.SEE_OTHER)


def pkgbase_disown_instance(request: Request, pkgbase: models.PackageBase):
    disowner = request.user
    notifs = [notify.DisownNotification(disowner.ID, pkgbase.ID)]

    is_maint = disowner == pkgbase.Maintainer
    if is_maint:
        with db.begin():
            # Comaintainer with the lowest Priority value; next-in-line.
            prio_comaint = pkgbase.comaintainers.order_by(
                models.PackageComaintainer.Priority.asc()
            ).first()
            if prio_comaint:
                # If there is such a comaintainer, promote them to maint.
                pkgbase.Maintainer = prio_comaint.User
                notifs.append(pkgutil.remove_comaintainer(prio_comaint))
            else:
                # Otherwise, just orphan the package completely.
                pkgbase.Maintainer = None
    elif request.user.has_credential(creds.PKGBASE_DISOWN):
        # Otherwise, the request user performing this disownage is a
        # Trusted User and we treat it like a standard orphan request.
        notifs += handle_request(request, ORPHAN_ID, pkgbase)
        with db.begin():
            pkgbase.Maintainer = None

    util.apply_all(notifs, lambda n: n.send())


@router.get("/pkgbase/{name}/disown")
@auth_required()
async def pkgbase_disown_get(request: Request, name: str):
    pkgbase = get_pkg_or_base(name, models.PackageBase)

    has_cred = request.user.has_credential(creds.PKGBASE_DISOWN,
                                           approved=[pkgbase.Maintainer])
    if not has_cred:
        return RedirectResponse(f"/pkgbase/{name}",
                                HTTPStatus.SEE_OTHER)

    context = make_context(request, "Disown Package")
    context["pkgbase"] = pkgbase
    return render_template(request, "packages/disown.html", context)


@router.post("/pkgbase/{name}/disown")
@auth_required()
async def pkgbase_disown_post(request: Request, name: str,
                              comments: str = Form(default=str()),
                              confirm: bool = Form(default=False)):
    pkgbase = get_pkg_or_base(name, models.PackageBase)

    has_cred = request.user.has_credential(creds.PKGBASE_DISOWN,
                                           approved=[pkgbase.Maintainer])
    if not has_cred:
        return RedirectResponse(f"/pkgbase/{name}",
                                HTTPStatus.SEE_OTHER)

    context = make_context(request, "Disown Package")
    context["pkgbase"] = pkgbase
    if not confirm:
        context["errors"] = [("The selected packages have not been disowned, "
                              "check the confirmation checkbox.")]
        return render_template(request, "packages/disown.html", context,
                               status_code=HTTPStatus.BAD_REQUEST)

    with db.begin():
        update_closure_comment(pkgbase, ORPHAN_ID, comments)

    try:
        pkgbase_disown_instance(request, pkgbase)
    except InvariantError as exc:
        context["errors"] = [str(exc)]
        return render_template(request, "packages/disown.html", context,
                               status_code=HTTPStatus.BAD_REQUEST)

    return RedirectResponse(f"/pkgbase/{name}",
                            status_code=HTTPStatus.SEE_OTHER)


def pkgbase_adopt_instance(request: Request, pkgbase: models.PackageBase):
    with db.begin():
        pkgbase.Maintainer = request.user

    notif = notify.AdoptNotification(request.user.ID, pkgbase.ID)
    notif.send()


@router.post("/pkgbase/{name}/adopt")
@auth_required()
async def pkgbase_adopt_post(request: Request, name: str):
    pkgbase = get_pkg_or_base(name, models.PackageBase)

    has_cred = request.user.has_credential(creds.PKGBASE_ADOPT)
    if has_cred or not pkgbase.Maintainer:
        # If the user has credentials, they'll adopt the package regardless
        # of maintainership. Otherwise, we'll promote the user to maintainer
        # if no maintainer currently exists.
        pkgbase_adopt_instance(request, pkgbase)

    return RedirectResponse(f"/pkgbase/{name}",
                            status_code=HTTPStatus.SEE_OTHER)


@router.get("/pkgbase/{name}/delete")
@auth_required()
async def pkgbase_delete_get(request: Request, name: str):
    if not request.user.has_credential(creds.PKGBASE_DELETE):
        return RedirectResponse(f"/pkgbase/{name}",
                                status_code=HTTPStatus.SEE_OTHER)

    context = make_context(request, "Package Deletion")
    context["pkgbase"] = get_pkg_or_base(name, models.PackageBase)
    return render_template(request, "packages/delete.html", context)


@router.post("/pkgbase/{name}/delete")
@auth_required()
async def pkgbase_delete_post(request: Request, name: str,
                              confirm: bool = Form(default=False),
                              comments: str = Form(default=str())):
    pkgbase = get_pkg_or_base(name, models.PackageBase)

    if not request.user.has_credential(creds.PKGBASE_DELETE):
        return RedirectResponse(f"/pkgbase/{name}",
                                status_code=HTTPStatus.SEE_OTHER)

    if not confirm:
        context = make_context(request, "Package Deletion")
        context["pkgbase"] = pkgbase
        context["errors"] = [("The selected packages have not been deleted, "
                              "check the confirmation checkbox.")]
        return render_template(request, "packages/delete.html", context,
                               status_code=HTTPStatus.BAD_REQUEST)

    if comments:
        # Update any existing deletion requests' ClosureComment.
        with db.begin():
            requests = pkgbase.requests.filter(
                and_(models.PackageRequest.Status == PENDING_ID,
                     models.PackageRequest.ReqTypeID == DELETION_ID)
            )
            for pkgreq in requests:
                pkgreq.ClosureComment = comments

    # Obtain deletion locks and delete the packages.
    packages = pkgbase.packages.all()
    for package in packages:
        delete_package(request, package, comments=comments)

    return RedirectResponse("/packages", status_code=HTTPStatus.SEE_OTHER)


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
        pkgbase_unflag_instance(request, pkgbase)
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
        pkgbase_notify_instance(request, pkgbase)

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
        pkgbase_unnotify_instance(request, pkgbase)

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
        pkgbase_adopt_instance(request, pkgbase)

    return (True, ["The selected packages have been adopted."])


def disown_all(request: Request, pkgbases: List[models.PackageBase]) \
        -> List[str]:
    errors = []
    for pkgbase in pkgbases:
        try:
            pkgbase_disown_instance(request, pkgbase)
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

    # A "memo" used to store names of packages that we delete.
    # We'll use this to log out a message about the deletions that occurred.
    deleted_pkgs = []

    # set-ify package_ids and query the database for related records.
    package_ids = set(package_ids)
    packages = db.query(models.Package).filter(
        models.Package.ID.in_(package_ids)).all()

    if len(packages) != len(package_ids):
        # Let the user know there was an issue with their input: they have
        # provided at least one package_id which does not exist in the DB.
        # TODO: This error has not yet been translated.
        return (False, ["One of the packages you selected does not exist."])

    # Now let's actually walk through and delete all of the packages,
    # using the same method we use in our /pkgbase/{name}/delete route.
    for pkg in packages:
        deleted_pkgs.append(pkg.Name)
        delete_package(request, pkg)

    # Log out the fact that this happened for accountability.
    logger.info(f"Privileged user '{request.user.Username}' deleted the "
                f"following packages: {str(deleted_pkgs)}.")

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


@router.get("/pkgbase/{name}/merge")
@auth_required()
async def pkgbase_merge_get(request: Request, name: str,
                            into: str = Query(default=str()),
                            next: str = Query(default=str())):
    pkgbase = get_pkg_or_base(name, models.PackageBase)

    if not next:
        next = f"/pkgbase/{pkgbase.Name}"

    context = make_context(request, "Package Merging")
    context.update({
        "pkgbase": pkgbase,
        "into": into,
        "next": next
    })

    status_code = HTTPStatus.OK
    # TODO: Lookup errors from credential instead of hardcoding them.
    # Idea: Something like credential_errors(creds.PKGBASE_MERGE).
    # Perhaps additionally: bad_credential_status_code(creds.PKGBASE_MERGE).
    # Don't take these examples verbatim. We should find good naming.
    if not request.user.has_credential(creds.PKGBASE_MERGE):
        context["errors"] = [
            "Only Trusted Users and Developers can merge packages."]
        status_code = HTTPStatus.UNAUTHORIZED

    return render_template(request, "pkgbase/merge.html", context,
                           status_code=status_code)


def pkgbase_merge_instance(request: Request, pkgbase: models.PackageBase,
                           target: models.PackageBase, comments: str = str()):
    pkgbasename = str(pkgbase.Name)

    # Create notifications.
    notifs = handle_request(request, MERGE_ID, pkgbase, target)

    # Target votes and notifications sets of user IDs that are
    # looking to be migrated.
    target_votes = set(v.UsersID for v in target.package_votes)
    target_notifs = set(n.UserID for n in target.notifications)

    with db.begin():
        # Merge pkgbase's comments.
        for comment in pkgbase.comments:
            comment.PackageBase = target

        # Merge notifications that don't yet exist in the target.
        for notif in pkgbase.notifications:
            if notif.UserID not in target_notifs:
                notif.PackageBase = target

        # Merge votes that don't yet exist in the target.
        for vote in pkgbase.package_votes:
            if vote.UsersID not in target_votes:
                vote.PackageBase = target

    # Run popupdate.
    popupdate.run_single(target)

    with db.begin():
        # Delete pkgbase and its packages now that everything's merged.
        for pkg in pkgbase.packages:
            db.delete(pkg)
        db.delete(pkgbase)

    # Log this out for accountability purposes.
    logger.info(f"Trusted User '{request.user.Username}' merged "
                f"'{pkgbasename}' into '{target.Name}'.")

    # Send notifications.
    util.apply_all(notifs, lambda n: n.send())


@router.post("/pkgbase/{name}/merge")
@auth_required()
async def pkgbase_merge_post(request: Request, name: str,
                             into: str = Form(default=str()),
                             comments: str = Form(default=str()),
                             confirm: bool = Form(default=False),
                             next: str = Form(default=str())):

    pkgbase = get_pkg_or_base(name, models.PackageBase)
    context = await make_variable_context(request, "Package Merging")
    context["pkgbase"] = pkgbase

    # TODO: Lookup errors from credential instead of hardcoding them.
    if not request.user.has_credential(creds.PKGBASE_MERGE):
        context["errors"] = [
            "Only Trusted Users and Developers can merge packages."]
        return render_template(request, "pkgbase/merge.html", context,
                               status_code=HTTPStatus.UNAUTHORIZED)

    if not confirm:
        context["errors"] = ["The selected packages have not been deleted, "
                             "check the confirmation checkbox."]
        return render_template(request, "pkgbase/merge.html", context,
                               status_code=HTTPStatus.BAD_REQUEST)

    try:
        target = get_pkg_or_base(into, models.PackageBase)
    except HTTPException:
        context["errors"] = [
            "Cannot find package to merge votes and comments into."]
        return render_template(request, "pkgbase/merge.html", context,
                               status_code=HTTPStatus.BAD_REQUEST)

    if pkgbase == target:
        context["errors"] = ["Cannot merge a package base with itself."]
        return render_template(request, "pkgbase/merge.html", context,
                               status_code=HTTPStatus.BAD_REQUEST)

    with db.begin():
        update_closure_comment(pkgbase, MERGE_ID, comments, target=target)

    # Merge pkgbase into target.
    pkgbase_merge_instance(request, pkgbase, target, comments=comments)

    # Run popupdate on the target.
    popupdate.run_single(target)

    if not next:
        next = f"/pkgbase/{target.Name}"

    # Redirect to the newly merged into package.
    return RedirectResponse(next, status_code=HTTPStatus.SEE_OTHER)
