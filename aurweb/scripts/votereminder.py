#!/usr/bin/env python3

from sqlalchemy import and_

import aurweb.config
from aurweb import db, time
from aurweb.models import VoteInfo
from aurweb.scripts import notify

notify_cmd = aurweb.config.get("notifications", "notify-cmd")


def main():
    db.get_engine()

    now = time.utcnow()

    start = aurweb.config.getint("votereminder", "range_start")
    filter_from = now + start

    end = aurweb.config.getint("votereminder", "range_end")
    filter_to = now + end

    query = db.query(VoteInfo.ID).filter(
        and_(VoteInfo.End >= filter_from, VoteInfo.End <= filter_to)
    )
    for voteinfo in query:
        notif = notify.VoteReminderNotification(voteinfo.ID)
        notif.send()


if __name__ == "__main__":
    main()
