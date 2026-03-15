#!/usr/bin/env python3

from sqlalchemy import and_, select

from aurweb import db, time
from aurweb.models import PackageBase


def _main() -> None:
    # One day behind.
    limit_to = time.utcnow() - 86400

    rows = (
        db.get_session()
        .execute(
            select(PackageBase).filter(
                and_(
                    PackageBase.SubmittedTS < limit_to,
                    PackageBase.PackagerUID.is_(None),
                )
            )
        )
        .scalars()
        .all()
    )
    db.delete_all(rows)


def main() -> None:
    # Previously used to clean up "reserved" packages which never got pushed.
    # Let's deactivate this for now since "setup-repo" is gone and we see
    # other issue where deletion of a user account might cause unintended
    # removal of a package (where PackagerUID account was deleted)
    return

    db.get_engine()
    with db.begin():
        _main()


if __name__ == "__main__":
    main()
