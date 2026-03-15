#!/usr/bin/env python3
from datetime import datetime

from sqlalchemy import and_, func, select
from sqlalchemy import update as sa_update
from sqlalchemy.sql.functions import coalesce
from sqlalchemy.sql.functions import sum as _sum

from aurweb import config, db, time
from aurweb.models import PackageBase, PackageVote


def run_variable(pkgbases: list[PackageBase] = []) -> None:
    """
    Update popularity on a list of PackageBases.

    If no PackageBase is included, we update the popularity
    of every PackageBase in the database.

    :param pkgbases: List of PackageBase instances
    """
    now = time.utcnow()

    # NumVotes subquery.
    votes_subq = (
        select(func.count("*"))
        .select_from(PackageVote)
        .where(PackageVote.PackageBaseID == PackageBase.ID)
    )

    # Popularity subquery.
    pop_subq = (
        select(
            coalesce(_sum(func.pow(0.98, (now - PackageVote.VoteTS) / 86400)), 0.0),
        )
        .select_from(PackageVote)
        .where(
            and_(
                PackageVote.PackageBaseID == PackageBase.ID,
                PackageVote.VoteTS.isnot(None),
            )
        )
    )

    with db.begin():
        stmt = sa_update(PackageBase).values(
            NumVotes=votes_subq.scalar_subquery(),
            Popularity=pop_subq.scalar_subquery(),
            PopularityUpdated=datetime.fromtimestamp(now),
        )

        if pkgbases:
            # If `pkgbases` were given, we should forcefully update the given
            # package base records' popularities.
            ids = {pkgbase.ID for pkgbase in pkgbases}
            stmt = stmt.where(PackageBase.ID.in_(ids))
        else:
            # Otherwise, we should only update popularities which have exceeded
            # the popularity interval length.
            interval = config.getint("git-archive", "popularity-interval")
            stmt = stmt.where(
                PackageBase.PopularityUpdated
                <= datetime.fromtimestamp((now - interval))
            )

        db.get_session().execute(stmt)


def run_single(pkgbase: PackageBase) -> None:
    """A single popupdate. The given pkgbase instance will be
    refreshed after the database update is done.

    NOTE: This function is compatible only with aurweb FastAPI.

    :param pkgbase: Instance of db.PackageBase
    """
    run_variable([pkgbase])
    db.refresh(pkgbase)


def main() -> None:
    db.get_engine()
    run_variable()


if __name__ == "__main__":
    main()
