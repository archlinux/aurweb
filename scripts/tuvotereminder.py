#!/usr/bin/python3

import configparser
import mysql.connector
import os
import subprocess
import time

config = configparser.RawConfigParser()
config.read(os.path.dirname(os.path.realpath(__file__)) + "/../conf/config")

aur_db_host = config.get('database', 'host')
aur_db_name = config.get('database', 'name')
aur_db_user = config.get('database', 'user')
aur_db_pass = config.get('database', 'password')
aur_db_socket = config.get('database', 'socket')
notify_cmd = config.get('notifications', 'notify-cmd')


def main():
    db = mysql.connector.connect(host=aur_db_host, user=aur_db_user,
                                 passwd=aur_db_pass, db=aur_db_name,
                                 unix_socket=aur_db_socket, buffered=True)
    cur = db.cursor()

    now = int(time.time())
    filter_from = now + 500
    filter_to = now + 172800

    cur.execute("SELECT ID FROM TU_VoteInfo WHERE End >= %s AND End <= %s",
                [filter_from, filter_to])

    for vote_id in [row[0] for row in cur.fetchall()]:
        subprocess.Popen((notify_cmd, 'tu-vote-reminder', str(vote_id)))


if __name__ == '__main__':
    main()
