#!/usr/bin/python3

from copy import copy, deepcopy
import configparser
import mysql.connector
import os
import pygit2
import re
import sys

import aurinfo

config = configparser.RawConfigParser()
config.read(os.path.dirname(os.path.realpath(__file__)) + "/../../conf/config")

aur_db_host = config.get('database', 'host')
aur_db_name = config.get('database', 'name')
aur_db_user = config.get('database', 'user')
aur_db_pass = config.get('database', 'password')

def save_srcinfo(srcinfo, db, cur, user):
    # Obtain package base ID and previous maintainer.
    pkgbase = srcinfo._pkgbase['pkgname']
    cur.execute("SELECT ID, MaintainerUID FROM PackageBases "
                "WHERE Name = %s", [pkgbase])
    (pkgbase_id, maintainer_uid) = cur.fetchone()
    was_orphan = not maintainer_uid

    # Obtain the user ID of the new maintainer.
    cur.execute("SELECT ID FROM Users WHERE Username = %s", [user])
    user_id = int(cur.fetchone()[0])

    # Update package base details and delete current packages.
    cur.execute("UPDATE PackageBases SET ModifiedTS = UNIX_TIMESTAMP(), " +
                "MaintainerUID = %s, PackagerUID = %s, " +
                "OutOfDateTS = NULL WHERE ID = %s",
                [user_id, user_id, pkgbase_id])
    cur.execute("DELETE FROM Packages WHERE PackageBaseID = %s",
                [pkgbase_id])

    for pkgname in srcinfo.GetPackageNames():
        pkginfo = srcinfo.GetMergedPackage(pkgname)

        if 'epoch' in pkginfo and pkginfo['epoch'] > 0:
            ver = '%d:%s-%s' % (pkginfo['epoch'], pkginfo['pkgver'],
                                pkginfo['pkgrel'])
        else:
            ver = '%s-%s' % (pkginfo['pkgver'], pkginfo['pkgrel'])

        # Create a new package.
        cur.execute("INSERT INTO Packages (PackageBaseID, Name, " +
                    "Version, Description, URL) " +
                    "VALUES (%s, %s, %s, %s, %s)",
                    [pkgbase_id, pkginfo['pkgname'], ver,
                     pkginfo['pkgdesc'], pkginfo['url']])
        db.commit()
        pkgid = cur.lastrowid

        # Add package sources.
        for source in pkginfo['source']:
            cur.execute("INSERT INTO PackageSources (PackageID, Source) " +
                        "VALUES (%s, %s)", [pkgid, source])

        # Add package dependencies.
        for deptype in ('depends', 'makedepends',
                        'checkdepends', 'optdepends'):
            if not deptype in pkginfo:
                continue
            cur.execute("SELECT ID FROM DependencyTypes WHERE Name = %s",
                        [deptype])
            deptypeid = cur.fetchone()[0]
            for dep in pkginfo[deptype]:
                depname = re.sub(r'(<|=|>).*', '', dep)
                depcond = dep[len(depname):]
                cur.execute("INSERT INTO PackageDepends (PackageID, " +
                            "DepTypeID, DepName, DepCondition) " +
                            "VALUES (%s, %s, %s, %s)", [pkgid, deptypeid,
                                                        depname, depcond])

        # Add package relations (conflicts, provides, replaces).
        for reltype in ('conflicts', 'provides', 'replaces'):
            if not reltype in pkginfo:
                continue
            cur.execute("SELECT ID FROM RelationTypes WHERE Name = %s",
                        [reltype])
            reltypeid = cur.fetchone()[0]
            for rel in pkginfo[reltype]:
                relname = re.sub(r'(<|=|>).*', '', rel)
                relcond = rel[len(relname):]
                cur.execute("INSERT INTO PackageRelations (PackageID, " +
                            "RelTypeID, RelName, RelCondition) " +
                            "VALUES (%s, %s, %s, %s)", [pkgid, reltypeid,
                                                        relname, relcond])

        # Add package licenses.
        if 'license' in pkginfo:
            for license in pkginfo['license']:
                cur.execute("SELECT ID FROM Licenses WHERE Name = %s",
                            [license])
                if cur.rowcount == 1:
                    licenseid = cur.fetchone()[0]
                else:
                    cur.execute("INSERT INTO Licenses (Name) VALUES (%s)",
                                [license])
                    db.commit()
                    licenseid = cur.lastrowid
                cur.execute("INSERT INTO PackageLicenses (PackageID, " +
                            "LicenseID) VALUES (%s, %s)",
                            [pkgid, licenseid])

        # Add package groups.
        if 'groups' in pkginfo:
            for group in pkginfo['groups']:
                cur.execute("SELECT ID FROM Groups WHERE Name = %s",
                            [group])
                if cur.rowcount == 1:
                    groupid = cur.fetchone()[0]
                else:
                    cur.execute("INSERT INTO Groups (Name) VALUES (%s)",
                                [group])
                    db.commit()
                    groupid = cur.lastrowid
                cur.execute("INSERT INTO PackageGroups (PackageID, "
                            "GroupID) VALUES (%s, %s)", [pkgid, groupid])

    # Add user to notification list on adoption.
    if was_orphan:
        cur.execute("INSERT INTO CommentNotify (PackageBaseID, UserID) " +
                    "VALUES (%s, %s)", [pkgbase_id, user_id])

    db.commit()

def die(msg):
    sys.stderr.write("error: %s\n" % (msg))
    exit(1)

def die_commit(msg, commit):
    sys.stderr.write("error: The following error " +
                     "occurred when parsing commit\n")
    sys.stderr.write("error: %s:\n" % (commit))
    sys.stderr.write("error: %s\n" % (msg))
    exit(1)

if len(sys.argv) != 4:
    die("invalid arguments")

refname = sys.argv[1]
sha1_old = sys.argv[2]
sha1_new = sys.argv[3]

user = os.environ.get("AUR_USER")
pkgbase = os.environ.get("AUR_PKGBASE")
git_dir = os.environ.get("AUR_GIT_DIR")

if refname != "refs/heads/master":
    die("pushing to a branch other than master is restricted")

repo = pygit2.Repository(git_dir)
walker = repo.walk(sha1_new, pygit2.GIT_SORT_TOPOLOGICAL)
if sha1_old != "0000000000000000000000000000000000000000":
    walker.hide(sha1_old)

for commit in walker:
    if not '.SRCINFO' in commit.tree:
        die_commit("missing .SRCINFO", commit.id)

    for treeobj in commit.tree:
        if repo[treeobj.id].size > 100000:
            die_commit("maximum blob size (100kB) exceeded", commit.id)

    srcinfo_raw = repo[commit.tree['.SRCINFO'].id].data.decode()
    srcinfo_raw = srcinfo_raw.split('\n')
    ecatcher = aurinfo.CollectionECatcher()
    srcinfo = aurinfo.ParseAurinfoFromIterable(srcinfo_raw, ecatcher)
    errors = ecatcher.Errors()
    if errors:
        sys.stderr.write("error: The following errors occurred "
                         "when parsing .SRCINFO in commit\n")
        sys.stderr.write("error: %s:\n" % (commit.id))
        for error in errors:
            sys.stderr.write("error: line %d: %s\n" % error)
        exit(1)

    srcinfo_pkgbase = srcinfo._pkgbase['pkgname']
    if srcinfo_pkgbase != pkgbase:
        die_commit('invalid pkgbase: %s' % (srcinfo_pkgbase), commit.id)

    for pkgname in srcinfo.GetPackageNames():
        pkginfo = srcinfo.GetMergedPackage(pkgname)

        if not re.match(r'[a-z0-9][a-z0-9\.+_-]*$', pkginfo['pkgname']):
            die_commit('invalid package name: %s' % (pkginfo['pkgname']),
                       commit.id)

        if not re.match(r'(?:http|ftp)s?://.*', pkginfo['url']):
            die_commit('invalid URL: %s' % (pkginfo['url']), commit.id)

        for field in ('pkgname', 'pkgdesc', 'url'):
            if len(pkginfo[field]) > 255:
                die_commit('%s field too long: %s' % (field, pkginfo[field]),
                           commit.id)

srcinfo_raw = repo[repo[sha1_new].tree['.SRCINFO'].id].data.decode()
srcinfo_raw = srcinfo_raw.split('\n')
srcinfo = aurinfo.ParseAurinfoFromIterable(srcinfo_raw)

db = mysql.connector.connect(host=aur_db_host, user=aur_db_user,
                             passwd=aur_db_pass, db=aur_db_name,
                             buffered=True)
cur = db.cursor()
save_srcinfo(srcinfo, db, cur, user)
db.close()
