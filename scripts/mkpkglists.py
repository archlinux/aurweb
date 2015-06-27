#!/usr/bin/python3

import configparser
import datetime
import gzip
import mysql.connector
import os

docroot = os.path.dirname(os.path.realpath(__file__)) + "/../web/html/"

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

datestr = datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
pkglist_header = "# AUR package list, generated on " + datestr
pkgbaselist_header = "# AUR package base list, generated on " + datestr

with gzip.open(docroot + "packages.gz", "w") as f:
    f.write(bytes(pkglist_header + "\n", "UTF-8"))
    cur.execute("SELECT Packages.Name FROM Packages INNER JOIN PackageBases " +
                "ON PackageBases.ID = Packages.PackageBaseID " +
                "WHERE PackageBases.PackagerUID IS NOT NULL")
    f.writelines([bytes(x[0] + "\n", "UTF-8") for x in cur.fetchall()])

with gzip.open(docroot + "pkgbase.gz", "w") as f:
    f.write(bytes(pkgbaselist_header + "\n", "UTF-8"))
    cur.execute("SELECT Name FROM PackageBases WHERE PackagerUID IS NOT NULL")
    f.writelines([bytes(x[0] + "\n", "UTF-8") for x in cur.fetchall()])

db.close()
