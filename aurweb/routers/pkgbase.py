from http import HTTPStatus

from fastapi import APIRouter, Form, HTTPException, Query, Request, Response
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy import and_

from aurweb import aur_logging, config, db, l10n, templates, time, util
from aurweb.auth import creds, requires_auth
from aurweb.exceptions import InvariantError, ValidationError, handle_form_exceptions
from aurweb.models import PackageBase
from aurweb.models.package_comment import PackageComment
from aurweb.models.package_keyword import PackageKeyword
from aurweb.models.package_notification import PackageNotification
from aurweb.models.package_request import ACCEPTED_ID, PENDING_ID, PackageRequest
from aurweb.models.package_vote import PackageVote
from aurweb.models.request_type import DELETION_ID, MERGE_ID, ORPHAN_ID
from aurweb.packages.requests import update_closure_comment
from aurweb.packages.util import get_pkg_or_base, get_pkgbase_comment
from aurweb.pkgbase import actions, util as pkgbaseutil, validate
from aurweb.scripts import notify, popupdate
from aurweb.scripts.rendercomment import update_comment_render_fastapi
from aurweb.templates import make_variable_context, render_template

logger = aur_logging.get_logger(__name__)
router = APIRouter()


@router.get("/pkgbase/{name}")
async def pkgbase(request: Request, name: str) -> Response:
    """
    Single package base view.

    :param request: FastAPI Request
    :param name: PackageBase.Name
    :return: HTMLResponse
    """
    # Get the PackageBase.
    pkgbase = get_pkg_or_base(name, PackageBase)

    # Redirect to /packages if there's only one related Package
    # and its name matches its PackageBase.
    packages = pkgbase.packages.all()
    pkg = packages[0]
    if len(packages) == 1 and pkg.Name == pkgbase.Name:
        return RedirectResponse(
            f"/packages/{pkg.Name}", status_code=int(HTTPStatus.SEE_OTHER)
        )

    # Add our base information.
    context = pkgbaseutil.make_context(request, pkgbase)
    context["packages"] = packages

    return render_template(request, "pkgbase/index.html", context)


@router.get("/pkgbase/{name}/voters")
async def pkgbase_voters(request: Request, name: str) -> Response:
    """
    View of package base voters.

    Requires `request.user` has creds.PKGBASE_LIST_VOTERS credential.

    :param request: FastAPI Request
    :param name: PackageBase.Name
    :return: HTMLResponse
    """
    # Get the PackageBase.
    pkgbase = get_pkg_or_base(name, PackageBase)

    if not request.user.has_credential(creds.PKGBASE_LIST_VOTERS):
        return RedirectResponse(f"/pkgbase/{name}", status_code=HTTPStatus.SEE_OTHER)

    context = templates.make_context(request, "Voters")
    context["pkgbase"] = pkgbase
    return render_template(request, "pkgbase/voters.html", context)


@router.get("/pkgbase/{name}/flag-comment")
async def pkgbase_flag_comment(request: Request, name: str):
    pkgbase = get_pkg_or_base(name, PackageBase)

    if pkgbase.OutOfDateTS is None:
        return RedirectResponse(f"/pkgbase/{name}", status_code=HTTPStatus.SEE_OTHER)

    context = templates.make_context(request, "Flag Comment")
    context["pkgbase"] = pkgbase
    return render_template(request, "pkgbase/flag-comment.html", context)


@db.async_retry_deadlock
@router.post("/pkgbase/{name}/keywords")
@handle_form_exceptions
async def pkgbase_keywords(
    request: Request, name: str, keywords: str = Form(default=str())
):
    pkgbase = get_pkg_or_base(name, PackageBase)

    approved = [pkgbase.Maintainer] + [c.User for c in pkgbase.comaintainers]
    has_cred = creds.has_credential(
        request.user, creds.PKGBASE_SET_KEYWORDS, approved=approved
    )
    if not has_cred:
        return Response(status_code=HTTPStatus.UNAUTHORIZED)

    # Lowercase all keywords. Our database table is case insensitive,
    # and providing CI duplicates of keywords is erroneous.
    keywords = set(k.lower() for k in keywords.split())

    # Delete all keywords which are not supplied by the user.
    with db.begin():
        other_keywords = pkgbase.keywords.filter(~PackageKeyword.Keyword.in_(keywords))
        other_keyword_strings = set(kwd.Keyword.lower() for kwd in other_keywords)

        existing_keywords = set(
            kwd.Keyword.lower()
            for kwd in pkgbase.keywords.filter(
                ~PackageKeyword.Keyword.in_(other_keyword_strings)
            )
        )

        db.delete_all(other_keywords)
        new_keywords = keywords.difference(existing_keywords)
        for keyword in new_keywords:
            db.create(PackageKeyword, PackageBase=pkgbase, Keyword=keyword)

    return RedirectResponse(f"/pkgbase/{name}", status_code=HTTPStatus.SEE_OTHER)


@router.get("/pkgbase/{name}/flag")
@requires_auth
async def pkgbase_flag_get(request: Request, name: str):
    pkgbase = get_pkg_or_base(name, PackageBase)

    has_cred = request.user.has_credential(creds.PKGBASE_FLAG)
    if not has_cred or pkgbase.OutOfDateTS is not None:
        return RedirectResponse(f"/pkgbase/{name}", status_code=HTTPStatus.SEE_OTHER)

    context = templates.make_context(request, "Flag Package Out-Of-Date")
    context["pkgbase"] = pkgbase
    return render_template(request, "pkgbase/flag.html", context)


@db.async_retry_deadlock
@router.post("/pkgbase/{name}/flag")
@handle_form_exceptions
@requires_auth
async def pkgbase_flag_post(
    request: Request, name: str, comments: str = Form(default=str())
):
    pkgbase = get_pkg_or_base(name, PackageBase)

    if not comments:
        context = templates.make_context(request, "Flag Package Out-Of-Date")
        context["pkgbase"] = pkgbase
        context["errors"] = [
            "The selected packages have not been flagged, " "please enter a comment."
        ]
        return render_template(
            request, "pkgbase/flag.html", context, status_code=HTTPStatus.BAD_REQUEST
        )

    has_cred = request.user.has_credential(creds.PKGBASE_FLAG)
    if has_cred and not pkgbase.OutOfDateTS:
        now = time.utcnow()
        with db.begin():
            pkgbase.OutOfDateTS = now
            pkgbase.Flagger = request.user
            pkgbase.FlaggerComment = comments

        notify.FlagNotification(request.user.ID, pkgbase.ID).send()

    return RedirectResponse(f"/pkgbase/{name}", status_code=HTTPStatus.SEE_OTHER)


@db.async_retry_deadlock
@router.post("/pkgbase/{name}/comments")
@handle_form_exceptions
@requires_auth
async def pkgbase_comments_post(
    request: Request,
    name: str,
    comment: str = Form(default=str()),
    enable_notifications: bool = Form(default=False),
):
    """Add a new comment via POST request."""
    pkgbase = get_pkg_or_base(name, PackageBase)

    if not comment:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST)

    # If the provided comment is different than the record's version,
    # update the db record.
    now = time.utcnow()
    with db.begin():
        comment = db.create(
            PackageComment,
            User=request.user,
            PackageBase=pkgbase,
            Comments=comment,
            RenderedComment=str(),
            CommentTS=now,
        )

        if enable_notifications and not request.user.notified(pkgbase):
            db.create(PackageNotification, User=request.user, PackageBase=pkgbase)
    update_comment_render_fastapi(comment)

    notif = notify.CommentNotification(request.user.ID, pkgbase.ID, comment.ID)
    notif.send()

    # Redirect to the pkgbase page.
    return RedirectResponse(
        f"/pkgbase/{pkgbase.Name}#comment-{comment.ID}",
        status_code=HTTPStatus.SEE_OTHER,
    )


@router.get("/pkgbase/{name}/comments/{id}/form")
@requires_auth
async def pkgbase_comment_form(
    request: Request, name: str, id: int, next: str = Query(default=None)
):
    """
    Produce a comment form for comment {id}.

    This route is used as a partial HTML endpoint when editing
    package comments via Javascript. This endpoint used to be
    part of the RPC as type=get-comment-form and has been
    relocated here because the form returned cannot be used
    externally and requires a POST request by the user.

    :param request: FastAPI Request
    :param name: PackageBase.Name
    :param id: PackageComment.ID
    :param next: Optional `next` value used for the comment form
    :return: JSONResponse
    """
    pkgbase = get_pkg_or_base(name, PackageBase)
    comment = pkgbase.comments.filter(PackageComment.ID == id).first()
    if not comment:
        return JSONResponse({}, status_code=HTTPStatus.NOT_FOUND)

    if not request.user.is_elevated() and request.user != comment.User:
        return JSONResponse({}, status_code=HTTPStatus.UNAUTHORIZED)

    context = pkgbaseutil.make_context(request, pkgbase)
    context["comment"] = comment

    if not next:
        next = f"/pkgbase/{name}"

    context["next"] = next

    form = templates.render_raw_template(
        request, "partials/packages/comment_form.html", context
    )
    return JSONResponse({"form": form})


@router.get("/pkgbase/{name}/comments/{id}/edit")
@requires_auth
async def pkgbase_comment_edit(
    request: Request, name: str, id: int, next: str = Form(default=None)
):
    """
    Render the non-javascript edit form.

    :param request: FastAPI Request
    :param name: PackageBase.Name
    :param id: PackageComment.ID
    :param next: Optional `next` parameter used in the POST request
    :return: HTMLResponse
    """
    pkgbase = get_pkg_or_base(name, PackageBase)
    comment = get_pkgbase_comment(pkgbase, id)

    if not next:
        next = f"/pkgbase/{name}"

    context = await make_variable_context(request, "Edit comment", next=next)
    context["comment"] = comment
    return render_template(request, "pkgbase/comments/edit.html", context)


@db.async_retry_deadlock
@router.post("/pkgbase/{name}/comments/{id}")
@handle_form_exceptions
@requires_auth
async def pkgbase_comment_post(
    request: Request,
    name: str,
    id: int,
    comment: str = Form(default=str()),
    enable_notifications: bool = Form(default=False),
    next: str = Form(default=None),
    cancel: bool = Form(default=False),
):
    """Edit an existing comment."""
    if cancel:
        return RedirectResponse(
            f"/pkgbase/{name}#comment-{id}", status_code=HTTPStatus.SEE_OTHER
        )

    pkgbase = get_pkg_or_base(name, PackageBase)
    db_comment = get_pkgbase_comment(pkgbase, id)

    if not comment:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST)
    elif request.user.ID != db_comment.UsersID:
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED)

    # If the provided comment is different than the record's version,
    # update the db record.
    now = time.utcnow()
    if db_comment.Comments != comment:
        with db.begin():
            db_comment.Comments = comment
            db_comment.Editor = request.user
            db_comment.EditedTS = now

    if enable_notifications:
        with db.begin():
            db_notif = request.user.notifications.filter(
                PackageNotification.PackageBaseID == pkgbase.ID
            ).first()
            if not db_notif:
                db.create(PackageNotification, User=request.user, PackageBase=pkgbase)

    update_comment_render_fastapi(db_comment)

    if not next:
        next = f"/pkgbase/{pkgbase.Name}"

    # Redirect to the pkgbase page anchored to the updated comment.
    return RedirectResponse(
        f"{next}#comment-{db_comment.ID}", status_code=HTTPStatus.SEE_OTHER
    )


@db.async_retry_deadlock
@router.post("/pkgbase/{name}/comments/{id}/pin")
@handle_form_exceptions
@requires_auth
async def pkgbase_comment_pin(
    request: Request, name: str, id: int, next: str = Form(default=None)
):
    """
    Pin a comment.

    :param request: FastAPI Request
    :param name: PackageBase.Name
    :param id: PackageComment.ID
    :param next: Optional `next` parameter used in the POST request
    :return: RedirectResponse to `next`
    """
    pkgbase = get_pkg_or_base(name, PackageBase)
    comment = get_pkgbase_comment(pkgbase, id)

    has_cred = request.user.has_credential(
        creds.COMMENT_PIN, approved=comment.maintainers()
    )
    if not has_cred:
        _ = l10n.get_translator_for_request(request)
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail=_("You are not allowed to pin this comment."),
        )

    now = time.utcnow()
    with db.begin():
        comment.PinnedTS = now

    if not next:
        next = f"/pkgbase/{name}"

    return RedirectResponse(next, status_code=HTTPStatus.SEE_OTHER)


@db.async_retry_deadlock
@router.post("/pkgbase/{name}/comments/{id}/unpin")
@handle_form_exceptions
@requires_auth
async def pkgbase_comment_unpin(
    request: Request, name: str, id: int, next: str = Form(default=None)
):
    """
    Unpin a comment.

    :param request: FastAPI Request
    :param name: PackageBase.Name
    :param id: PackageComment.ID
    :param next: Optional `next` parameter used in the POST request
    :return: RedirectResponse to `next`
    """
    pkgbase = get_pkg_or_base(name, PackageBase)
    comment = get_pkgbase_comment(pkgbase, id)

    has_cred = request.user.has_credential(
        creds.COMMENT_PIN, approved=comment.maintainers()
    )
    if not has_cred:
        _ = l10n.get_translator_for_request(request)
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail=_("You are not allowed to unpin this comment."),
        )

    with db.begin():
        comment.PinnedTS = 0

    if not next:
        next = f"/pkgbase/{name}"

    return RedirectResponse(next, status_code=HTTPStatus.SEE_OTHER)


@db.async_retry_deadlock
@router.post("/pkgbase/{name}/comments/{id}/delete")
@handle_form_exceptions
@requires_auth
async def pkgbase_comment_delete(
    request: Request, name: str, id: int, next: str = Form(default=None)
):
    """
    Delete a comment.

    This action does **not** delete the comment from the database, but
    sets PackageBase.DelTS and PackageBase.DeleterUID, which is used to
    decide who gets to view the comment and what utilities it gets.

    :param request: FastAPI Request
    :param name: PackageBase.Name
    :param id: PackageComment.ID
    :param next: Optional `next` parameter used in the POST request
    :return: RedirectResposne to `next`
    """
    pkgbase = get_pkg_or_base(name, PackageBase)
    comment = get_pkgbase_comment(pkgbase, id)

    authorized = request.user.has_credential(creds.COMMENT_DELETE, [comment.User])
    if not authorized:
        _ = l10n.get_translator_for_request(request)
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail=_("You are not allowed to delete this comment."),
        )

    now = time.utcnow()
    with db.begin():
        comment.Deleter = request.user
        comment.DelTS = now

    if not next:
        next = f"/pkgbase/{name}"

    return RedirectResponse(next, status_code=HTTPStatus.SEE_OTHER)


@db.async_retry_deadlock
@router.post("/pkgbase/{name}/comments/{id}/undelete")
@handle_form_exceptions
@requires_auth
async def pkgbase_comment_undelete(
    request: Request, name: str, id: int, next: str = Form(default=None)
):
    """
    Undelete a comment.

    This action does **not** undelete any comment from the database, but
    unsets PackageBase.DelTS and PackageBase.DeleterUID which restores
    the comment to a standard state.

    :param request: FastAPI Request
    :param name: PackageBase.Name
    :param id: PackageComment.ID
    :param next: Optional `next` parameter used in the POST request
    :return: RedirectResponse to `next`
    """
    pkgbase = get_pkg_or_base(name, PackageBase)
    comment = get_pkgbase_comment(pkgbase, id)

    has_cred = request.user.has_credential(
        creds.COMMENT_UNDELETE, approved=[comment.User]
    )
    if not has_cred:
        _ = l10n.get_translator_for_request(request)
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail=_("You are not allowed to undelete this comment."),
        )

    with db.begin():
        comment.Deleter = None
        comment.DelTS = None

    if not next:
        next = f"/pkgbase/{name}"

    return RedirectResponse(next, status_code=HTTPStatus.SEE_OTHER)


@db.async_retry_deadlock
@router.post("/pkgbase/{name}/vote")
@handle_form_exceptions
@requires_auth
async def pkgbase_vote(request: Request, name: str):
    pkgbase = get_pkg_or_base(name, PackageBase)

    vote = pkgbase.package_votes.filter(PackageVote.UsersID == request.user.ID).first()
    has_cred = request.user.has_credential(creds.PKGBASE_VOTE)
    if has_cred and not vote:
        now = time.utcnow()
        with db.begin():
            db.create(PackageVote, User=request.user, PackageBase=pkgbase, VoteTS=now)

        # Update NumVotes/Popularity.
        popupdate.run_single(pkgbase)

    return RedirectResponse(f"/pkgbase/{name}", status_code=HTTPStatus.SEE_OTHER)


@db.async_retry_deadlock
@router.post("/pkgbase/{name}/unvote")
@handle_form_exceptions
@requires_auth
async def pkgbase_unvote(request: Request, name: str):
    pkgbase = get_pkg_or_base(name, PackageBase)

    vote = pkgbase.package_votes.filter(PackageVote.UsersID == request.user.ID).first()
    has_cred = request.user.has_credential(creds.PKGBASE_VOTE)
    if has_cred and vote:
        with db.begin():
            db.delete(vote)

        # Update NumVotes/Popularity.
        popupdate.run_single(pkgbase)

    return RedirectResponse(f"/pkgbase/{name}", status_code=HTTPStatus.SEE_OTHER)


@db.async_retry_deadlock
@router.post("/pkgbase/{name}/notify")
@handle_form_exceptions
@requires_auth
async def pkgbase_notify(request: Request, name: str):
    pkgbase = get_pkg_or_base(name, PackageBase)
    actions.pkgbase_notify_instance(request, pkgbase)
    return RedirectResponse(f"/pkgbase/{name}", status_code=HTTPStatus.SEE_OTHER)


@db.async_retry_deadlock
@router.post("/pkgbase/{name}/unnotify")
@handle_form_exceptions
@requires_auth
async def pkgbase_unnotify(request: Request, name: str):
    pkgbase = get_pkg_or_base(name, PackageBase)
    actions.pkgbase_unnotify_instance(request, pkgbase)
    return RedirectResponse(f"/pkgbase/{name}", status_code=HTTPStatus.SEE_OTHER)


@db.async_retry_deadlock
@router.post("/pkgbase/{name}/unflag")
@handle_form_exceptions
@requires_auth
async def pkgbase_unflag(request: Request, name: str):
    pkgbase = get_pkg_or_base(name, PackageBase)
    actions.pkgbase_unflag_instance(request, pkgbase)
    return RedirectResponse(f"/pkgbase/{name}", status_code=HTTPStatus.SEE_OTHER)


@router.get("/pkgbase/{name}/disown")
@requires_auth
async def pkgbase_disown_get(
    request: Request, name: str, next: str = Query(default=str())
):
    pkgbase = get_pkg_or_base(name, PackageBase)

    comaints = {c.User for c in pkgbase.comaintainers}
    approved = [pkgbase.Maintainer] + list(comaints)
    has_cred = request.user.has_credential(creds.PKGBASE_DISOWN, approved=approved)
    if not has_cred:
        return RedirectResponse(f"/pkgbase/{name}", HTTPStatus.SEE_OTHER)

    context = templates.make_context(request, "Disown Package")
    context["pkgbase"] = pkgbase
    context["next"] = next or "/pkgbase/{name}"
    context["is_maint"] = request.user == pkgbase.Maintainer
    context["is_comaint"] = request.user in comaints
    return render_template(request, "pkgbase/disown.html", context)


@db.async_retry_deadlock
@router.post("/pkgbase/{name}/disown")
@handle_form_exceptions
@requires_auth
async def pkgbase_disown_post(
    request: Request,
    name: str,
    comments: str = Form(default=str()),
    confirm: bool = Form(default=False),
    next: str = Form(default=str()),
):
    pkgbase = get_pkg_or_base(name, PackageBase)

    comaints = {c.User for c in pkgbase.comaintainers}
    approved = [pkgbase.Maintainer] + list(comaints)
    has_cred = request.user.has_credential(creds.PKGBASE_DISOWN, approved=approved)
    if not has_cred:
        return RedirectResponse(f"/pkgbase/{name}", HTTPStatus.SEE_OTHER)

    context = templates.make_context(request, "Disown Package")
    context["pkgbase"] = pkgbase
    context["is_maint"] = request.user == pkgbase.Maintainer
    context["is_comaint"] = request.user in comaints

    if not confirm:
        context["errors"] = [
            (
                "The selected packages have not been disowned, "
                "check the confirmation checkbox."
            )
        ]
        return render_template(
            request, "pkgbase/disown.html", context, status_code=HTTPStatus.BAD_REQUEST
        )

    if request.user != pkgbase.Maintainer and request.user not in comaints:
        with db.begin():
            update_closure_comment(pkgbase, ORPHAN_ID, comments)

    try:
        actions.pkgbase_disown_instance(request, pkgbase)
    except InvariantError as exc:
        context["errors"] = [str(exc)]
        return render_template(
            request, "pkgbase/disown.html", context, status_code=HTTPStatus.BAD_REQUEST
        )

    next = next or f"/pkgbase/{name}"
    return RedirectResponse(next, status_code=HTTPStatus.SEE_OTHER)


@db.async_retry_deadlock
@router.post("/pkgbase/{name}/adopt")
@handle_form_exceptions
@requires_auth
async def pkgbase_adopt_post(request: Request, name: str):
    pkgbase = get_pkg_or_base(name, PackageBase)

    has_cred = request.user.has_credential(creds.PKGBASE_ADOPT)
    if has_cred or not pkgbase.Maintainer:
        # If the user has credentials, they'll adopt the package regardless
        # of maintainership. Otherwise, we'll promote the user to maintainer
        # if no maintainer currently exists.
        actions.pkgbase_adopt_instance(request, pkgbase)

    return RedirectResponse(f"/pkgbase/{name}", status_code=HTTPStatus.SEE_OTHER)


@router.get("/pkgbase/{name}/comaintainers")
@requires_auth
async def pkgbase_comaintainers(request: Request, name: str) -> Response:
    # Get the PackageBase.
    pkgbase = get_pkg_or_base(name, PackageBase)

    # Unauthorized users (Non-TU/Dev and not the pkgbase maintainer)
    # get redirected to the package base's page.
    has_creds = request.user.has_credential(
        creds.PKGBASE_EDIT_COMAINTAINERS, approved=[pkgbase.Maintainer]
    )
    if not has_creds:
        return RedirectResponse(f"/pkgbase/{name}", status_code=HTTPStatus.SEE_OTHER)

    # Add our base information.
    context = templates.make_context(request, "Manage Co-maintainers")
    context.update(
        {
            "pkgbase": pkgbase,
            "comaintainers": [c.User.Username for c in pkgbase.comaintainers],
        }
    )

    return render_template(request, "pkgbase/comaintainers.html", context)


@db.async_retry_deadlock
@router.post("/pkgbase/{name}/comaintainers")
@handle_form_exceptions
@requires_auth
async def pkgbase_comaintainers_post(
    request: Request, name: str, users: str = Form(default=str())
) -> Response:
    # Get the PackageBase.
    pkgbase = get_pkg_or_base(name, PackageBase)

    # Unauthorized users (Non-TU/Dev and not the pkgbase maintainer)
    # get redirected to the package base's page.
    has_creds = request.user.has_credential(
        creds.PKGBASE_EDIT_COMAINTAINERS, approved=[pkgbase.Maintainer]
    )
    if not has_creds:
        return RedirectResponse(f"/pkgbase/{name}", status_code=HTTPStatus.SEE_OTHER)

    users = {e.strip() for e in users.split("\n") if bool(e.strip())}
    records = {c.User.Username for c in pkgbase.comaintainers}

    users_to_rm = records.difference(users)
    pkgbaseutil.remove_comaintainers(pkgbase, users_to_rm)
    logger.debug(
        f"{request.user} removed comaintainers from " f"{pkgbase.Name}: {users_to_rm}"
    )

    users_to_add = users.difference(records)
    error = pkgbaseutil.add_comaintainers(request, pkgbase, users_to_add)
    if error:
        context = templates.make_context(request, "Manage Co-maintainers")
        context["pkgbase"] = pkgbase
        context["comaintainers"] = [c.User.Username for c in pkgbase.comaintainers]
        context["errors"] = [error]
        return render_template(request, "pkgbase/comaintainers.html", context)

    logger.debug(
        f"{request.user} added comaintainers to " f"{pkgbase.Name}: {users_to_add}"
    )

    return RedirectResponse(
        f"/pkgbase/{pkgbase.Name}", status_code=HTTPStatus.SEE_OTHER
    )


@router.get("/pkgbase/{name}/request")
@requires_auth
async def pkgbase_request(
    request: Request, name: str, next: str = Query(default=str())
):
    pkgbase = get_pkg_or_base(name, PackageBase)
    context = await make_variable_context(request, "Submit Request")
    context["pkgbase"] = pkgbase
    context["next"] = next or f"/pkgbase/{name}"
    return render_template(request, "pkgbase/request.html", context)


@db.async_retry_deadlock
@router.post("/pkgbase/{name}/request")
@handle_form_exceptions
@requires_auth
async def pkgbase_request_post(
    request: Request,
    name: str,
    type: str = Form(...),
    merge_into: str = Form(default=None),
    comments: str = Form(default=str()),
    next: str = Form(default=str()),
):
    pkgbase = get_pkg_or_base(name, PackageBase)

    # Create our render context.
    context = await make_variable_context(request, "Submit Request")
    context["pkgbase"] = pkgbase

    types = {"deletion": DELETION_ID, "merge": MERGE_ID, "orphan": ORPHAN_ID}

    if type not in types:
        # In the case that someone crafted a POST request with an invalid
        # type, just return them to the request form with BAD_REQUEST status.
        return render_template(
            request, "pkgbase/request.html", context, status_code=HTTPStatus.BAD_REQUEST
        )

    try:
        validate.request(pkgbase, type, comments, merge_into, context)
    except ValidationError as exc:
        logger.error(f"Request Validation Error: {str(exc.data)}")
        context["errors"] = exc.data
        return render_template(request, "pkgbase/request.html", context)

    # All good. Create a new PackageRequest based on the given type.
    now = time.utcnow()
    with db.begin():
        pkgreq = db.create(
            PackageRequest,
            ReqTypeID=types.get(type),
            User=request.user,
            RequestTS=now,
            PackageBase=pkgbase,
            PackageBaseName=pkgbase.Name,
            MergeBaseName=merge_into,
            Comments=comments,
            ClosureComment=str(),
        )

    # Prepare notification object.
    notif = notify.RequestOpenNotification(
        request.user.ID,
        pkgreq.ID,
        type,
        pkgreq.PackageBase.ID,
        merge_into=merge_into or None,
    )

    # Send the notification now that we're out of the DB scope.
    notif.send()

    auto_orphan_age = config.getint("options", "auto_orphan_age")
    auto_delete_age = config.getint("options", "auto_delete_age")

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
            request.user.ID, pkgreq.ID, pkgreq.status_display()
        )
        notif.send()
        logger.debug(f"New request #{pkgreq.ID} is marked for auto-orphan.")
    elif type == "deletion" and is_maintainer and outdated:
        # This request should be auto-accepted.
        notifs = actions.pkgbase_delete_instance(request, pkgbase, comments=comments)
        util.apply_all(notifs, lambda n: n.send())
        logger.debug(f"New request #{pkgreq.ID} is marked for auto-deletion.")

    # Redirect the submitting user to /packages.
    return RedirectResponse("/packages", status_code=HTTPStatus.SEE_OTHER)


@router.get("/pkgbase/{name}/delete")
@requires_auth
async def pkgbase_delete_get(
    request: Request, name: str, next: str = Query(default=str())
):
    if not request.user.has_credential(creds.PKGBASE_DELETE):
        return RedirectResponse(f"/pkgbase/{name}", status_code=HTTPStatus.SEE_OTHER)

    context = templates.make_context(request, "Package Deletion")
    context["pkgbase"] = get_pkg_or_base(name, PackageBase)
    context["next"] = next or "/packages"
    return render_template(request, "pkgbase/delete.html", context)


@db.async_retry_deadlock
@router.post("/pkgbase/{name}/delete")
@handle_form_exceptions
@requires_auth
async def pkgbase_delete_post(
    request: Request,
    name: str,
    confirm: bool = Form(default=False),
    comments: str = Form(default=str()),
    next: str = Form(default="/packages"),
):
    pkgbase = get_pkg_or_base(name, PackageBase)

    if not request.user.has_credential(creds.PKGBASE_DELETE):
        return RedirectResponse(f"/pkgbase/{name}", status_code=HTTPStatus.SEE_OTHER)

    if not confirm:
        context = templates.make_context(request, "Package Deletion")
        context["pkgbase"] = pkgbase
        context["errors"] = [
            (
                "The selected packages have not been deleted, "
                "check the confirmation checkbox."
            )
        ]
        return render_template(
            request, "pkgbase/delete.html", context, status_code=HTTPStatus.BAD_REQUEST
        )

    if comments:
        # Update any existing deletion requests' ClosureComment.
        with db.begin():
            requests = pkgbase.requests.filter(
                and_(
                    PackageRequest.Status == PENDING_ID,
                    PackageRequest.ReqTypeID == DELETION_ID,
                )
            )
            for pkgreq in requests:
                pkgreq.ClosureComment = comments

    notifs = actions.pkgbase_delete_instance(request, pkgbase, comments=comments)
    util.apply_all(notifs, lambda n: n.send())
    return RedirectResponse(next, status_code=HTTPStatus.SEE_OTHER)


@router.get("/pkgbase/{name}/merge")
@requires_auth
async def pkgbase_merge_get(
    request: Request,
    name: str,
    into: str = Query(default=str()),
    next: str = Query(default=str()),
):
    pkgbase = get_pkg_or_base(name, PackageBase)

    context = templates.make_context(request, "Package Merging")
    context.update({"pkgbase": pkgbase, "into": into, "next": next})

    status_code = HTTPStatus.OK
    # TODO: Lookup errors from credential instead of hardcoding them.
    # Idea: Something like credential_errors(creds.PKGBASE_MERGE).
    # Perhaps additionally: bad_credential_status_code(creds.PKGBASE_MERGE).
    # Don't take these examples verbatim. We should find good naming.
    if not request.user.has_credential(creds.PKGBASE_MERGE):
        context["errors"] = ["Only Trusted Users and Developers can merge packages."]
        status_code = HTTPStatus.UNAUTHORIZED

    return render_template(
        request, "pkgbase/merge.html", context, status_code=status_code
    )


@db.async_retry_deadlock
@router.post("/pkgbase/{name}/merge")
@handle_form_exceptions
@requires_auth
async def pkgbase_merge_post(
    request: Request,
    name: str,
    into: str = Form(default=str()),
    comments: str = Form(default=str()),
    confirm: bool = Form(default=False),
    next: str = Form(default=str()),
):
    pkgbase = get_pkg_or_base(name, PackageBase)
    context = await make_variable_context(request, "Package Merging")
    context["pkgbase"] = pkgbase

    # TODO: Lookup errors from credential instead of hardcoding them.
    if not request.user.has_credential(creds.PKGBASE_MERGE):
        context["errors"] = ["Only Trusted Users and Developers can merge packages."]
        return render_template(
            request, "pkgbase/merge.html", context, status_code=HTTPStatus.UNAUTHORIZED
        )

    if not confirm:
        context["errors"] = [
            "The selected packages have not been deleted, "
            "check the confirmation checkbox."
        ]
        return render_template(
            request, "pkgbase/merge.html", context, status_code=HTTPStatus.BAD_REQUEST
        )

    try:
        target = get_pkg_or_base(into, PackageBase)
    except HTTPException:
        context["errors"] = ["Cannot find package to merge votes and comments into."]
        return render_template(
            request, "pkgbase/merge.html", context, status_code=HTTPStatus.BAD_REQUEST
        )

    if pkgbase == target:
        context["errors"] = ["Cannot merge a package base with itself."]
        return render_template(
            request, "pkgbase/merge.html", context, status_code=HTTPStatus.BAD_REQUEST
        )

    with db.begin():
        update_closure_comment(pkgbase, MERGE_ID, comments, target=target)

    # Merge pkgbase into target.
    actions.pkgbase_merge_instance(request, pkgbase, target, comments=comments)

    if not next:
        next = f"/pkgbase/{target.Name}"

    # Redirect to the newly merged into package.
    return RedirectResponse(next, status_code=HTTPStatus.SEE_OTHER)
