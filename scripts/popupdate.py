#!/usr/bin/python3

import configparser
import mysql.connector
import os

config = configparser.RawConfigParser()
config.read(os.path.dirname(os.path.realpath(__file__)) + "/../conf/config")

aur_db_host = config.get('database', 'host')
aur_db_name = config.get('database', 'name')
aur_db_user = config.get('database', 'user')
aur_db_pass = config.get('database', 'password')
aur_db_socket = config.get('database', 'socket')

db = mysql.connector.connect(host=aur_db_host, user=aur_db_user,
                             passwd=aur_db_pass, db=aur_db_name,
                             unix_socket=aur_db_socket, buffered=True)
cur = db.cursor()

cur.execute("UPDATE PackageBases SET NumVotes = (SELECT COUNT(*) FROM " +
            "PackageVotes WHERE PackageVotes.PackageBaseID = PackageBases.ID)")

cur.execute("UPDATE PackageBases SET Popularity = (" +
            "SELECT SUM(POWER(0.98, (UNIX_TIMESTAMP() - VoteTS) / 86400)) " +
            "FROM PackageVotes WHERE PackageVotes.PackageBaseID = " +
            "PackageBases.ID AND NOT VoteTS IS NULL)")

db.commit()
db.close()
