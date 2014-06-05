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

repo_base_path = config.get('serve', 'repo-base')
repo_regex = config.get('serve', 'repo-regex')
git_update_hook = config.get('serve', 'git-update-hook')
git_shell_cmd = config.get('serve', 'git-shell-cmd')

def repo_path_validate(path):
    if not path.startswith(repo_base_path):
        return False
    if not path.endswith('.git/'):
        return False
    repo = path[len(repo_base_path):-5]
    return re.match(repo_regex, repo)

def repo_path_get_pkgbase(path):
    pkgbase = path.rstrip('/').rpartition('/')[2]
    if pkgbase.endswith('.git'):
        pkgbase = pkgbase[:-4]
    return pkgbase

def setup_repo(repo, user):
    if not re.match(repo_regex, repo):
        die('invalid repository name: %s' % (repo))

    db = mysql.connector.connect(host=aur_db_host, user=aur_db_user,
                                 passwd=aur_db_pass, db=aur_db_name)
    cur = db.cursor()

    cur.execute("SELECT COUNT(*) FROM PackageBases WHERE Name = %s ", [repo])
    if cur.fetchone()[0] > 0:
        die('package base already exists: %s' % (repo))

    cur.execute("SELECT ID FROM Users WHERE Username = %s ", [user])
    userid = cur.fetchone()[0]
    if userid == 0:
        die('unknown user: %s' % (user))

    cur.execute("INSERT INTO PackageBases (Name, SubmittedTS, ModifiedTS, " +
                "SubmitterUID) VALUES (%s, UNIX_TIMESTAMP(), " +
                "UNIX_TIMESTAMP(), %s)", [repo, userid])

    db.commit()
    db.close()

    repo_path = repo_base_path + '/' + repo + '.git/'
    pygit2.init_repository(repo_path, True)
    os.symlink(git_update_hook, repo_path + 'hooks/update')

def check_permissions(pkgbase, user):
    db = mysql.connector.connect(host=aur_db_host, user=aur_db_user,
                                 passwd=aur_db_pass, db=aur_db_name,
                                 buffered=True)
    cur = db.cursor()

    cur.execute("SELECT COUNT(*) FROM PackageBases INNER JOIN Users " +
                "ON Users.ID = PackageBases.MaintainerUID OR " +
                "PackageBases.MaintainerUID IS NULL WHERE " +
                "Name = %s AND Username = %s", [pkgbase, user])
    return cur.fetchone()[0] > 0

def die(msg):
    sys.stderr.write("%s\n" % (msg))
    exit(1)

user = sys.argv[1]
cmd = os.environ.get("SSH_ORIGINAL_COMMAND")
if not cmd:
    die('no command specified')
cmdargv = shlex.split(cmd)
action = cmdargv[0]

if action == 'git-upload-pack' or action == 'git-receive-pack':
    path = cmdargv[1]
    if not repo_path_validate(path):
        die('invalid path: %s' % (path))
    pkgbase = repo_path_get_pkgbase(path)
    if action == 'git-receive-pack':
        if not check_permissions(pkgbase, user):
            die('permission denied: %s' % (user))
    os.environ["AUR_USER"] = user
    os.environ["AUR_GIT_DIR"] = path
    os.environ["AUR_PKGBASE"] = pkgbase
    os.execl(git_shell_cmd, git_shell_cmd, '-c', cmd)
elif action == 'setup-repo':
    if len(cmdargv) < 2:
        die('missing repository name')
    setup_repo(cmdargv[1], user)
else:
    die('invalid command: %s' % (action))
