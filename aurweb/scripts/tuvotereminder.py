#!/usr/bin/env python3

import subprocess
import time

import aurweb.config
import aurweb.db

notify_cmd = aurweb.config.get('notifications', 'notify-cmd')


def main():
    conn = aurweb.db.Connection()

    now = int(time.time())
    filter_from = now + 500
    filter_to = now + 172800

    cur = conn.execute("SELECT ID FROM TU_VoteInfo " +
                       "WHERE End >= ? AND End <= ?",
                       [filter_from, filter_to])

    for vote_id in [row[0] for row in cur.fetchall()]:
        subprocess.Popen((notify_cmd, 'tu-vote-reminder', str(vote_id))).wait()


if __name__ == '__main__':
    main()
