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
git_update_hook = config.get('serve', 'git-update-hook')
git_shell_cmd = config.get('serve', 'git-shell-cmd')
ssh_cmdline = config.get('serve', 'ssh-cmdline')

def repo_path_validate(path):
    if not path.startswith(repo_base_path):
        return False
    if path.endswith('.git'):
        repo = path[len(repo_base_path):-4]
    elif path.endswith('.git/'):
        repo = path[len(repo_base_path):-5]
    else:
        return False
    return re.match(repo_regex, repo)

def repo_path_get_pkgbase(path):
    pkgbase = path.rstrip('/').rpartition('/')[2]
    if pkgbase.endswith('.git'):
        pkgbase = pkgbase[:-4]
    return pkgbase

def list_repos(user):
    db = mysql.connector.connect(host=aur_db_host, user=aur_db_user,
                                 passwd=aur_db_pass, db=aur_db_name,
                                 unix_socket=aur_db_socket)
    cur = db.cursor()

    cur.execute("SELECT ID FROM Users WHERE Username = %s ", [user])
    userid = cur.fetchone()[0]
    if userid == 0:
        die('%s: unknown user: %s' % (action, user))

    cur.execute("SELECT Name, PackagerUID FROM PackageBases " +
                "WHERE MaintainerUID = %s ", [userid])
    for row in cur:
        print((' ' if row[1] else '*') + row[0])
    db.close()

def setup_repo(repo, user):
    if not re.match(repo_regex, repo):
        die('%s: invalid repository name: %s' % (action, repo))

    db = mysql.connector.connect(host=aur_db_host, user=aur_db_user,
                                 passwd=aur_db_pass, db=aur_db_name,
                                 unix_socket=aur_db_socket)
    cur = db.cursor()

    cur.execute("SELECT COUNT(*) FROM PackageBases WHERE Name = %s ", [repo])
    if cur.fetchone()[0] > 0:
        die('%s: package base already exists: %s' % (action, repo))

    cur.execute("SELECT ID FROM Users WHERE Username = %s ", [user])
    userid = cur.fetchone()[0]
    if userid == 0:
        die('%s: unknown user: %s' % (action, user))

    cur.execute("INSERT INTO PackageBases (Name, SubmittedTS, ModifiedTS, " +
                "SubmitterUID, MaintainerUID) VALUES (%s, UNIX_TIMESTAMP(), " +
                "UNIX_TIMESTAMP(), %s, %s)", [repo, userid, userid])

    db.commit()
    db.close()

    repo_path = repo_base_path + '/' + repo + '.git/'
    pygit2.init_repository(repo_path, True)
    os.symlink(git_update_hook, repo_path + 'hooks/update')

def check_permissions(pkgbase, user):
    db = mysql.connector.connect(host=aur_db_host, user=aur_db_user,
                                 passwd=aur_db_pass, db=aur_db_name,
                                 unix_socket=aur_db_socket, buffered=True)
    cur = db.cursor()

    cur.execute("SELECT COUNT(*) FROM PackageBases INNER JOIN Users " +
                "ON Users.ID = PackageBases.MaintainerUID OR " +
                "PackageBases.MaintainerUID IS NULL WHERE " +
                "Name = %s AND Username = %s", [pkgbase, user])
    return cur.fetchone()[0] > 0

def die(msg):
    sys.stderr.write("%s\n" % (msg))
    exit(1)

def die_with_help(msg):
    die(msg + "\nTry `%s help` for a list of commands." % (ssh_cmdline))

user = sys.argv[1]
cmd = os.environ.get("SSH_ORIGINAL_COMMAND")
if not cmd:
    die_with_help("Interactive shell is disabled.")
cmdargv = shlex.split(cmd)
action = cmdargv[0]

if action == 'git-upload-pack' or action == 'git-receive-pack':
    if len(cmdargv) < 2:
        die_with_help("%s: missing path" % (action))
    path = repo_base_path.rstrip('/') + cmdargv[1]
    if not repo_path_validate(path):
        die('%s: invalid path: %s' % (action, path))
    pkgbase = repo_path_get_pkgbase(path)
    if not os.path.exists(path):
        setup_repo(pkgbase, user)
    if action == 'git-receive-pack':
        if not check_permissions(pkgbase, user):
            die('%s: permission denied: %s' % (action, user))
    os.environ["AUR_USER"] = user
    os.environ["AUR_GIT_DIR"] = path
    os.environ["AUR_PKGBASE"] = pkgbase
    cmd = action + " '" + path + "'"
    os.execl(git_shell_cmd, git_shell_cmd, '-c', cmd)
elif action == 'list-repos':
    if len(cmdargv) > 1:
        die_with_help("%s: too many arguments" % (action))
    list_repos(user)
elif action == 'setup-repo':
    if len(cmdargv) < 2:
        die_with_help("%s: missing repository name" % (action))
    if len(cmdargv) > 2:
        die_with_help("%s: too many arguments" % (action))
    setup_repo(cmdargv[1], user)
elif action == 'help':
    die("Commands:\n" +
        "  help                 Show this help message and exit.\n" +
        "  list-repos           List all your repositories.\n" +
        "  setup-repo <name>    Create an empty repository.\n" +
        "  git-receive-pack     Internal command used with Git.\n" +
        "  git-upload-pack      Internal command used with Git.")
else:
    die_with_help("invalid command: %s" % (action))
