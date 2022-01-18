#!/usr/bin/env python3

from sqlalchemy import and_

import aurweb.config

from aurweb import db, time
from aurweb.models import TUVoteInfo
from aurweb.scripts import notify

notify_cmd = aurweb.config.get('notifications', 'notify-cmd')


def main():
    db.get_engine()

    now = time.utcnow()

    start = aurweb.config.getint("tuvotereminder", "range_start")
    filter_from = now + start

    end = aurweb.config.getint("tuvotereminder", "range_end")
    filter_to = now + end

    query = db.query(TUVoteInfo.ID).filter(
        and_(TUVoteInfo.End >= filter_from,
             TUVoteInfo.End <= filter_to)
    )
    for voteinfo in query:
        notif = notify.TUVoteReminderNotification(voteinfo.ID)
        notif.send()


if __name__ == '__main__':
    main()
