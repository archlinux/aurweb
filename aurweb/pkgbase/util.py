from typing import Any, Dict

from fastapi import Request

from aurweb import config
from aurweb.models import PackageBase
from aurweb.models.package_comment import PackageComment
from aurweb.models.package_request import PackageRequest
from aurweb.models.package_vote import PackageVote
from aurweb.templates import make_context as _make_context


def make_context(request: Request, pkgbase: PackageBase) -> Dict[str, Any]:
    """ Make a basic context for package or pkgbase.

    :param request: FastAPI request
    :param pkgbase: PackageBase instance
    :return: A pkgbase context without specific differences
    """
    context = _make_context(request, pkgbase.Name)

    context["git_clone_uri_anon"] = config.get("options", "git_clone_uri_anon")
    context["git_clone_uri_priv"] = config.get("options", "git_clone_uri_priv")
    context["pkgbase"] = pkgbase
    context["packages_count"] = pkgbase.packages.count()
    context["keywords"] = pkgbase.keywords
    context["comments"] = pkgbase.comments.order_by(
        PackageComment.CommentTS.desc()
    )
    context["pinned_comments"] = pkgbase.comments.filter(
        PackageComment.PinnedTS != 0
    ).order_by(PackageComment.CommentTS.desc())

    context["is_maintainer"] = bool(request.user == pkgbase.Maintainer)
    context["notified"] = request.user.notified(pkgbase)

    context["out_of_date"] = bool(pkgbase.OutOfDateTS)

    context["voted"] = request.user.package_votes.filter(
        PackageVote.PackageBaseID == pkgbase.ID
    ).scalar()

    context["requests"] = pkgbase.requests.filter(
        PackageRequest.ClosedTS.is_(None)
    ).count()

    return context
