#!/usr/bin/python3

import configparser
import mysql.connector
import os
import pygit2
import re
import shlex
import sys

config = configparser.RawConfigParser()
config.read(os.path.dirname(os.path.realpath(__file__)) + "/../../conf/config")

aur_db_host = config.get('database', 'host')
aur_db_name = config.get('database', 'name')
aur_db_user = config.get('database', 'user')
aur_db_pass = config.get('database', 'password')
aur_db_socket = config.get('database', 'socket')

repo_base_path = config.get('serve', 'repo-base')
repo_regex = config.get('serve', 'repo-regex')
template_path = config.get('serve', 'template-path')

def die(msg):
    sys.stderr.write("%s\n" % (msg))
    exit(1)

db = mysql.connector.connect(host=aur_db_host, user=aur_db_user,
                             passwd=aur_db_pass, db=aur_db_name,
                             unix_socket=aur_db_socket)
cur = db.cursor()

cur.execute("SELECT Name FROM PackageBases")
repos = [row[0] for row in cur]
db.close()

for repo in repos:
    if not re.match(repo_regex, repo):
        die('invalid repository name: %s' % (repo))

i = 1
n = len(repos)

for repo in repos:
    print("[%s/%d] %s" % (str(i).rjust(len(str(n))), n, repo))

    repo_path = repo_base_path + '/' + repo + '.git/'
    pygit2.init_repository(repo_path, True, 48, template_path=template_path)

    i += 1
