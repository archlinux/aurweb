#!/usr/bin/env python3

from sqlalchemy import and_, func
from sqlalchemy.sql.functions import coalesce
from sqlalchemy.sql.functions import sum as _sum

from aurweb import db, time
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
    votes_subq = db.get_session().query(
        func.count("*")
    ).select_from(PackageVote).filter(
        PackageVote.PackageBaseID == PackageBase.ID
    )

    # Popularity subquery.
    pop_subq = db.get_session().query(
        coalesce(_sum(func.pow(0.98, (now - PackageVote.VoteTS) / 86400)), 0.0),
    ).select_from(PackageVote).filter(
        and_(PackageVote.PackageBaseID == PackageBase.ID,
             PackageVote.VoteTS.isnot(None))
    )

    with db.begin():
        query = db.query(PackageBase)

        ids = set()
        if pkgbases:
            ids = {pkgbase.ID for pkgbase in pkgbases}
            query = query.filter(PackageBase.ID.in_(ids))

        query.update({
            "NumVotes": votes_subq.scalar_subquery(),
            "Popularity": pop_subq.scalar_subquery()
        })


def run_single(pkgbase: PackageBase) -> None:
    """ A single popupdate. The given pkgbase instance will be
    refreshed after the database update is done.

    NOTE: This function is compatible only with aurweb FastAPI.

    :param pkgbase: Instance of db.PackageBase
    """
    run_variable([pkgbase])
    db.refresh(pkgbase)


def main():
    db.get_engine()
    run_variable()


if __name__ == '__main__':
    main()
