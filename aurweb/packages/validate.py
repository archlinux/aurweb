from typing import Any, Dict

from aurweb import db, models
from aurweb.exceptions import ValidationError


def request(pkgbase: models.PackageBase,
            type: str, comments: str, merge_into: str,
            context: Dict[str, Any]) -> None:
    if not comments:
        raise ValidationError(["The comment field must not be empty."])

    if type == "merge":
        # Perform merge-related checks.
        if not merge_into:
            # TODO: This error needs to be translated.
            raise ValidationError(
                ['The "Merge into" field must not be empty.'])

        target = db.query(models.PackageBase).filter(
            models.PackageBase.Name == merge_into
        ).first()
        if not target:
            # TODO: This error needs to be translated.
            raise ValidationError([
                "The package base you want to merge into does not exist."
            ])

        db.refresh(target)
        if target.ID == pkgbase.ID:
            # TODO: This error needs to be translated.
            raise ValidationError([
                "You cannot merge a package base into itself."
            ])
