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
config.read(os.path.dirname(os.path.realpath(__file__)) + "/../conf/config")

aur_db_host = config.get('database', 'host')
aur_db_name = config.get('database', 'name')
aur_db_user = config.get('database', 'user')
aur_db_pass = config.get('database', 'password')
aur_db_socket = config.get('database', 'socket')

repo_path = config.get('serve', 'repo-path')
repo_regex = config.get('serve', 'repo-regex')

def extract_arch_fields(pkginfo, field):
    values = []

    if field in pkginfo:
        for val in pkginfo[field]:
            values.append({"value": val, "arch": None})

    for arch in ['i686', 'x86_64']:
        if field + '_' + arch in pkginfo:
            for val in pkginfo[field + '_' + arch]:
                values.append({"value": val, "arch": arch})

    return values

def parse_dep(depstring):
    dep, _, desc = depstring.partition(': ')
    depname = re.sub(r'(<|=|>).*', '', dep)
    depcond = dep[len(depname):]

    if (desc):
        return (depname + ': ' + desc, depcond)
    else:
        return (depname, depcond)

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
                "PackagerUID = %s, OutOfDateTS = NULL WHERE ID = %s",
                [user_id, pkgbase_id])
    cur.execute("UPDATE PackageBases SET MaintainerUID = %s " +
                "WHERE ID = %s AND MaintainerUID IS NULL",
                [user_id, pkgbase_id])
    cur.execute("DELETE FROM Packages WHERE PackageBaseID = %s",
                [pkgbase_id])

    for pkgname in srcinfo.GetPackageNames():
        pkginfo = srcinfo.GetMergedPackage(pkgname)

        if 'epoch' in pkginfo and int(pkginfo['epoch']) > 0:
            ver = '{:d}:{:s}-{:s}'.format(int(pkginfo['epoch']), pkginfo['pkgver'],
                                          pkginfo['pkgrel'])
        else:
            ver = '{:s}-{:s}'.format(pkginfo['pkgver'], pkginfo['pkgrel'])

        for field in ('pkgdesc', 'url'):
            if not field in pkginfo:
                pkginfo[field] = None

        # Create a new package.
        cur.execute("INSERT INTO Packages (PackageBaseID, Name, " +
                    "Version, Description, URL) " +
                    "VALUES (%s, %s, %s, %s, %s)",
                    [pkgbase_id, pkginfo['pkgname'], ver,
                     pkginfo['pkgdesc'], pkginfo['url']])
        db.commit()
        pkgid = cur.lastrowid

        # Add package sources.
        for source_info in extract_arch_fields(pkginfo, 'source'):
            cur.execute("INSERT INTO PackageSources (PackageID, Source, " +
                        "SourceArch) VALUES (%s, %s, %s)",
                        [pkgid, source_info['value'], source_info['arch']])

        # Add package dependencies.
        for deptype in ('depends', 'makedepends',
                        'checkdepends', 'optdepends'):
            cur.execute("SELECT ID FROM DependencyTypes WHERE Name = %s",
                        [deptype])
            deptypeid = cur.fetchone()[0]
            for dep_info in extract_arch_fields(pkginfo, deptype):
                depname, depcond = parse_dep(dep_info['value'])
                deparch = dep_info['arch']
                cur.execute("INSERT INTO PackageDepends (PackageID, " +
                            "DepTypeID, DepName, DepCondition, DepArch) " +
                            "VALUES (%s, %s, %s, %s, %s)",
                            [pkgid, deptypeid, depname, depcond, deparch])

        # Add package relations (conflicts, provides, replaces).
        for reltype in ('conflicts', 'provides', 'replaces'):
            cur.execute("SELECT ID FROM RelationTypes WHERE Name = %s",
                        [reltype])
            reltypeid = cur.fetchone()[0]
            for rel_info in extract_arch_fields(pkginfo, reltype):
                relname, relcond = parse_dep(rel_info['value'])
                relarch = rel_info['arch']
                cur.execute("INSERT INTO PackageRelations (PackageID, " +
                            "RelTypeID, RelName, RelCondition, RelArch) " +
                            "VALUES (%s, %s, %s, %s, %s)",
                            [pkgid, reltypeid, relname, relcond, relarch])

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
        cur.execute("SELECT COUNT(*) FROM CommentNotify WHERE " +
                    "PackageBaseID = %s AND UserID = %s",
                    [pkgbase_id, user_id])
        if cur.fetchone()[0] == 0:
            cur.execute("INSERT INTO CommentNotify (PackageBaseID, UserID) " +
                        "VALUES (%s, %s)", [pkgbase_id, user_id])

    db.commit()

def die(msg):
    sys.stderr.write("error: {:s}\n".format(msg))
    exit(1)

def die_commit(msg, commit):
    sys.stderr.write("error: The following error " +
                     "occurred when parsing commit\n")
    sys.stderr.write("error: {:s}:\n".format(commit))
    sys.stderr.write("error: {:s}\n".format(msg))
    exit(1)

if len(sys.argv) != 4:
    die("invalid arguments")

refname = sys.argv[1]
sha1_old = sys.argv[2]
sha1_new = sys.argv[3]

user = os.environ.get("AUR_USER")
pkgbase = os.environ.get("AUR_PKGBASE")
privileged = (os.environ.get("AUR_PRIVILEGED", '0') == '1')

if refname != "refs/heads/master":
    die("pushing to a branch other than master is restricted")

repo = pygit2.Repository(repo_path)

db = mysql.connector.connect(host=aur_db_host, user=aur_db_user,
                             passwd=aur_db_pass, db=aur_db_name,
                             unix_socket=aur_db_socket, buffered=True)
cur = db.cursor()

# Detect and deny non-fast-forwards.
if sha1_old != "0000000000000000000000000000000000000000":
    walker = repo.walk(sha1_old, pygit2.GIT_SORT_TOPOLOGICAL)
    walker.hide(sha1_new)
    if next(walker, None) != None:
        cur.execute("SELECT AccountTypeID FROM Users WHERE UserName = %s ",
                    [user])
        if cur.fetchone()[0] == 1:
            die("denying non-fast-forward (you should pull first)")

# Prepare the walker that validates new commits.
walker = repo.walk(sha1_new, pygit2.GIT_SORT_TOPOLOGICAL)
if sha1_old != "0000000000000000000000000000000000000000":
    walker.hide(sha1_old)

cur.execute("SELECT Name FROM PackageBlacklist")
blacklist = [row[0] for row in cur.fetchall()]

for commit in walker:
    if not '.SRCINFO' in commit.tree:
        die_commit("missing .SRCINFO", str(commit.id))

    for treeobj in commit.tree:
        blob = repo[treeobj.id]

        if isinstance(blob, pygit2.Tree):
            die_commit("the repository must not contain subdirectories",
                       str(commit.id))

        if not isinstance(blob, pygit2.Blob):
            die_commit("not a blob object: {:s}".format(treeobj), str(commit.id))

        if blob.size > 250000:
            die_commit("maximum blob size (250kB) exceeded", str(commit.id))

    srcinfo_raw = repo[commit.tree['.SRCINFO'].id].data.decode()
    srcinfo_raw = srcinfo_raw.split('\n')
    ecatcher = aurinfo.CollectionECatcher()
    srcinfo = aurinfo.ParseAurinfoFromIterable(srcinfo_raw, ecatcher)
    errors = ecatcher.Errors()
    if errors:
        sys.stderr.write("error: The following errors occurred "
                         "when parsing .SRCINFO in commit\n")
        sys.stderr.write("error: {:s}:\n".format(str(commit.id)))
        for error in errors:
            sys.stderr.write("error: line {:d}: {:s}\n".format(*error))
        exit(1)

    srcinfo_pkgbase = srcinfo._pkgbase['pkgname']
    if not re.match(repo_regex, srcinfo_pkgbase):
        die_commit('invalid pkgbase: {:s}'.format(srcinfo_pkgbase), str(commit.id))

    for pkgname in srcinfo.GetPackageNames():
        pkginfo = srcinfo.GetMergedPackage(pkgname)

        for field in ('pkgver', 'pkgrel', 'pkgname'):
            if not field in pkginfo:
                die_commit('missing mandatory field: {:s}'.format(field), str(commit.id))

        if 'epoch' in pkginfo and not pkginfo['epoch'].isdigit():
            die_commit('invalid epoch: {:s}'.format(pkginfo['epoch']), str(commit.id))

        if not re.match(r'[a-z0-9][a-z0-9\.+_-]*$', pkginfo['pkgname']):
            die_commit('invalid package name: {:s}'.format(pkginfo['pkgname']),
                       str(commit.id))

        for field in ('pkgname', 'pkgdesc', 'url'):
            if field in pkginfo and len(pkginfo[field]) > 255:
                die_commit('{:s} field too long: {:s}'.format(field, pkginfo[field]),
                           str(commit.id))

        for field in ('install', 'changelog'):
            if field in pkginfo and not pkginfo[field] in commit.tree:
                die_commit('missing {:s} file: {:s}'.format(field, pkginfo[field]),
                           str(commit.id))

        for field in extract_arch_fields(pkginfo, 'source'):
            fname = field['value']
            if "://" in fname or "lp:" in fname:
                continue
            if not fname in commit.tree:
                die_commit('missing source file: {:s}'.format(fname), str(commit.id))

srcinfo_raw = repo[repo[sha1_new].tree['.SRCINFO'].id].data.decode()
srcinfo_raw = srcinfo_raw.split('\n')
srcinfo = aurinfo.ParseAurinfoFromIterable(srcinfo_raw)

srcinfo_pkgbase = srcinfo._pkgbase['pkgname']
if srcinfo_pkgbase != pkgbase:
    die('invalid pkgbase: {:s}, expected {:s}'.format(srcinfo_pkgbase, pkgbase))

pkgbase = srcinfo._pkgbase['pkgname']
cur.execute("SELECT ID FROM PackageBases WHERE Name = %s", [pkgbase])
pkgbase_id = cur.fetchone()[0]

for pkgname in srcinfo.GetPackageNames():
    pkginfo = srcinfo.GetMergedPackage(pkgname)
    pkgname = pkginfo['pkgname']

    if pkgname in blacklist and not privileged:
        die('package is blacklisted: {:s}'.format(pkginfo['pkgname']))

    cur.execute("SELECT COUNT(*) FROM Packages WHERE Name = %s AND " +
                "PackageBaseID <> %s", [pkgname, pkgbase_id])
    if cur.fetchone()[0] > 0:
        die('cannot overwrite package: {:s}'.format(pkgname))

save_srcinfo(srcinfo, db, cur, user)

db.close()

# Create (or update) a branch with the name of the package base for better
# accessibility.
repo.create_reference('refs/heads/' + pkgbase, sha1_new, True)

# Work around a Git bug: The HEAD ref is not updated when using gitnamespaces.
# This can be removed once the bug fix is included in Git mainline. See
# http://git.661346.n2.nabble.com/PATCH-receive-pack-Create-a-HEAD-ref-for-ref-namespace-td7632149.html
# for details.
repo.create_reference('refs/namespaces/' + pkgbase + '/HEAD', sha1_new, True)
