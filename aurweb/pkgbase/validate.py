from typing import Any

from aurweb import db
from aurweb.exceptions import ValidationError
from aurweb.models import PackageBase


def request(
    pkgbase: PackageBase,
    type: str,
    comments: str,
    merge_into: str,
    context: dict[str, Any],
) -> None:
    if not comments:
        raise ValidationError(["The comment field must not be empty."])

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
