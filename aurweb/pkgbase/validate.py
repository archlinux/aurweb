from http import HTTPStatus
from typing import Any

from fastapi import HTTPException

from aurweb import config, db
from aurweb.exceptions import ValidationError
from aurweb.models import PackageBase


def request(
    pkgbase: PackageBase,
    type: str,
    comments: str,
    merge_into: str,
    context: dict[str, Any],
) -> None:
    # validate comment
    comment(comments)

    if type == "merge":
        # Perform merge-related checks.
        if not merge_into:
            # TODO: This error needs to be translated.
            raise ValidationError(['The "Merge into" field must not be empty.'])

        target = db.query(PackageBase).filter(PackageBase.Name == merge_into).first()
        if not target:
            # TODO: This error needs to be translated.
            raise ValidationError(
                ["The package base you want to merge into does not exist."]
            )

        db.refresh(target)
        if target.ID == pkgbase.ID:
            # TODO: This error needs to be translated.
            raise ValidationError(["You cannot merge a package base into itself."])


def comment(comment: str):
    if not comment:
        raise ValidationError(["The comment field must not be empty."])

    if len(comment) > config.getint("options", "max_chars_comment", 5000):
        raise ValidationError(["Maximum number of characters for comment exceeded."])


def comment_raise_http_ex(comments: str):
    try:
        comment(comments)
    except ValidationError as err:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail=err.data[0],
        )
