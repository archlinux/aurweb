#!/usr/bin/env python3

from sqlalchemy import and_, select

import aurweb.config
from aurweb import db, time
from aurweb.models import VoteInfo
from aurweb.scripts import notify

notify_cmd = aurweb.config.get("notifications", "notify-cmd")


def main() -> None:
    db.get_engine()

    now = time.utcnow()

    start = aurweb.config.getint("votereminder", "range_start")
    assert start is not None, "range_start is missing in votereminder second"
    filter_from = now + start

    end = aurweb.config.getint("votereminder", "range_end")
    assert end is not None, "range_end is missing in votereminder section"
    filter_to = now + end

    vote_ids = (
        db.get_session()
        .execute(
            select(VoteInfo.ID).filter(
                and_(VoteInfo.End >= filter_from, VoteInfo.End <= filter_to)
            )
        )
        .scalars()
    )
    for vote_id in vote_ids:
        notif = notify.VoteReminderNotification(vote_id)
        notif.send()


if __name__ == "__main__":
    main()
