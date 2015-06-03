#!/usr/bin/python3

import configparser
import mysql.connector
import os
import pyalpm

config = configparser.RawConfigParser()
config.read(os.path.dirname(os.path.realpath(__file__)) + "/../conf/config")

aur_db_host = config.get('database', 'host')
aur_db_name = config.get('database', 'name')
aur_db_user = config.get('database', 'user')
aur_db_pass = config.get('database', 'password')
aur_db_socket = config.get('database', 'socket')
db_path = config.get('aurblup', 'db-path')
sync_dbs = config.get('aurblup', 'sync-dbs').split(' ')
servers = config.get('aurblup', 'servers').split(' ')

blacklist = set()

h = pyalpm.Handle("/", db_path)
for sync_db in sync_dbs:
    repo = h.register_syncdb(sync_db, pyalpm.SIG_DATABASE_OPTIONAL)
    repo.servers = [server.replace("%s", sync_db) for server in servers]
    t = h.init_transaction()
    repo.update(False)
    t.release()

    for pkg in repo.pkgcache:
        blacklist.add(pkg.name)
        [blacklist.add(x) for x in pkg.replaces]

db = mysql.connector.connect(host=aur_db_host, user=aur_db_user,
                             passwd=aur_db_pass, db=aur_db_name,
                             unix_socket=aur_db_socket, buffered=True)
cur = db.cursor()

cur.execute("SELECT Name FROM PackageBlacklist")
oldblacklist = set([row[0] for row in cur.fetchall()])

for pkg in blacklist.difference(oldblacklist):
    cur.execute("INSERT INTO PackageBlacklist (Name) VALUES (%s)", [pkg])
for pkg in oldblacklist.difference(blacklist):
    cur.execute("DELETE FROM PackageBlacklist WHERE Name = %s", [pkg])

db.commit()
db.close()
