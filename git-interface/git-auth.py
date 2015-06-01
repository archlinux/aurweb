#!/usr/bin/python3

import configparser
import mysql.connector
import os
import re
import sys

config = configparser.RawConfigParser()
config.read(os.path.dirname(os.path.realpath(__file__)) + "/../conf/config")

aur_db_host = config.get('database', 'host')
aur_db_name = config.get('database', 'name')
aur_db_user = config.get('database', 'user')
aur_db_pass = config.get('database', 'password')
aur_db_socket = config.get('database', 'socket')

valid_keytypes = config.get('auth', 'valid-keytypes').split()
username_regex = config.get('auth', 'username-regex')
git_serve_cmd = config.get('auth', 'git-serve-cmd')
ssh_opts = config.get('auth', 'ssh-options')

keytype = sys.argv[1]
keytext = sys.argv[2]
if not keytype in valid_keytypes:
    exit(1)

db = mysql.connector.connect(host=aur_db_host, user=aur_db_user,
                             passwd=aur_db_pass, db=aur_db_name,
                             unix_socket=aur_db_socket, buffered=True)

cur = db.cursor()
cur.execute("SELECT Username FROM Users WHERE SSHPubKey = %s " +
            "AND Suspended = 0", (keytype + " " + keytext,))

if cur.rowcount != 1:
    exit(1)

user = cur.fetchone()[0]
if not re.match(username_regex, user):
    exit(1)

print('command="%s %s",%s %s' % (git_serve_cmd, user, ssh_opts,
    keytype + " " + keytext))
