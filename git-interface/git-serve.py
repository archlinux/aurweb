#!/usr/bin/python3

import configparser
import mysql.connector
import os
import re
import shlex
import sys

config = configparser.RawConfigParser()
config.read(os.path.dirname(os.path.realpath(__file__)) + "/../conf/config")

aur_db_host = config.get('database', 'host')
aur_db_name = config.get('database', 'name')
aur_db_user = config.get('database', 'user')
aur_db_pass = config.get('database', 'password')
aur_db_socket = config.get('database', 'socket')

repo_path = config.get('serve', 'repo-path')
repo_regex = config.get('serve', 'repo-regex')
git_shell_cmd = config.get('serve', 'git-shell-cmd')
git_update_cmd = config.get('serve', 'git-update-cmd')
ssh_cmdline = config.get('serve', 'ssh-cmdline')

enable_maintenance = config.getboolean('options', 'enable-maintenance')
maintenance_exc = config.get('options', 'maintenance-exceptions').split()


def pkgbase_from_name(pkgbase):
    db = mysql.connector.connect(host=aur_db_host, user=aur_db_user,
                                 passwd=aur_db_pass, db=aur_db_name,
                                 unix_socket=aur_db_socket)
    cur = db.cursor()
    cur.execute("SELECT ID FROM PackageBases WHERE Name = %s", [pkgbase])
    db.close()

    row = cur.fetchone()
    return row[0] if row else None


def pkgbase_exists(pkgbase):
    return pkgbase_from_name(pkgbase) is not None


def list_repos(user):
    db = mysql.connector.connect(host=aur_db_host, user=aur_db_user,
                                 passwd=aur_db_pass, db=aur_db_name,
                                 unix_socket=aur_db_socket)
    cur = db.cursor()

    cur.execute("SELECT ID FROM Users WHERE Username = %s ", [user])
    userid = cur.fetchone()[0]
    if userid == 0:
        die('{:s}: unknown user: {:s}'.format(action, user))

    cur.execute("SELECT Name, PackagerUID FROM PackageBases " +
                "WHERE MaintainerUID = %s ", [userid])
    for row in cur:
        print((' ' if row[1] else '*') + row[0])
    db.close()


def create_pkgbase(pkgbase, user):
    if not re.match(repo_regex, pkgbase):
        die('{:s}: invalid repository name: {:s}'.format(action, pkgbase))
    if pkgbase_exists(pkgbase):
        die('{:s}: package base already exists: {:s}'.format(action, pkgbase))

    db = mysql.connector.connect(host=aur_db_host, user=aur_db_user,
                                 passwd=aur_db_pass, db=aur_db_name,
                                 unix_socket=aur_db_socket)
    cur = db.cursor()

    cur.execute("SELECT ID FROM Users WHERE Username = %s ", [user])
    userid = cur.fetchone()[0]
    if userid == 0:
        die('{:s}: unknown user: {:s}'.format(action, user))

    cur.execute("INSERT INTO PackageBases (Name, SubmittedTS, ModifiedTS, " +
                "SubmitterUID, MaintainerUID) VALUES (%s, UNIX_TIMESTAMP(), " +
                "UNIX_TIMESTAMP(), %s, %s)", [pkgbase, userid, userid])
    pkgbase_id = cur.lastrowid

    cur.execute("INSERT INTO PackageNotifications (PackageBaseID, UserID) " +
                "VALUES (%s, %s)", [pkgbase_id, userid])

    db.commit()
    db.close()


def pkgbase_set_keywords(pkgbase, keywords):
    pkgbase_id = pkgbase_from_name(pkgbase)
    if not pkgbase_id:
        die('{:s}: package base not found: {:s}'.format(action, pkgbase))

    db = mysql.connector.connect(host=aur_db_host, user=aur_db_user,
                                 passwd=aur_db_pass, db=aur_db_name,
                                 unix_socket=aur_db_socket)
    cur = db.cursor()

    cur.execute("DELETE FROM PackageKeywords WHERE PackageBaseID = %s",
                [pkgbase_id])
    for keyword in keywords:
        cur.execute("INSERT INTO PackageKeywords (PackageBaseID, Keyword) "
                    "VALUES (%s, %s)", [pkgbase_id, keyword])

    db.commit()
    db.close()


def check_permissions(pkgbase, user):
    db = mysql.connector.connect(host=aur_db_host, user=aur_db_user,
                                 passwd=aur_db_pass, db=aur_db_name,
                                 unix_socket=aur_db_socket, buffered=True)
    cur = db.cursor()

    if os.environ.get('AUR_PRIVILEGED', '0') == '1':
        return True

    cur.execute("SELECT COUNT(*) FROM PackageBases " +
                "LEFT JOIN PackageComaintainers " +
                "ON PackageComaintainers.PackageBaseID = PackageBases.ID " +
                "INNER JOIN Users ON Users.ID = PackageBases.MaintainerUID " +
                "OR PackageBases.MaintainerUID IS NULL " +
                "OR Users.ID = PackageComaintainers.UsersID " +
                "WHERE Name = %s AND Username = %s", [pkgbase, user])
    return cur.fetchone()[0] > 0


def die(msg):
    sys.stderr.write("{:s}\n".format(msg))
    exit(1)


def die_with_help(msg):
    die(msg + "\nTry `{:s} help` for a list of commands.".format(ssh_cmdline))


user = os.environ.get("AUR_USER")
cmd = os.environ.get("SSH_ORIGINAL_COMMAND")
if not cmd:
    die_with_help("Interactive shell is disabled.")
cmdargv = shlex.split(cmd)
action = cmdargv[0]

if enable_maintenance:
    remote_addr = os.environ["SSH_CLIENT"].split(" ")[0]
    if remote_addr not in maintenance_exc:
        die("The AUR is down due to maintenance. We will be back soon.")

if action == 'git-upload-pack' or action == 'git-receive-pack':
    if len(cmdargv) < 2:
        die_with_help("{:s}: missing path".format(action))

    path = cmdargv[1].rstrip('/')
    if not path.startswith('/'):
        path = '/' + path
    if not path.endswith('.git'):
        path = path + '.git'
    pkgbase = path[1:-4]
    if not re.match(repo_regex, pkgbase):
        die('{:s}: invalid repository name: {:s}'.format(action, pkgbase))

    if not pkgbase_exists(pkgbase):
        create_pkgbase(pkgbase, user)

    if action == 'git-receive-pack':
        if not check_permissions(pkgbase, user):
            die('{:s}: permission denied: {:s}'.format(action, user))

    os.environ["AUR_USER"] = user
    os.environ["AUR_PKGBASE"] = pkgbase
    os.environ["GIT_NAMESPACE"] = pkgbase
    cmd = action + " '" + repo_path + "'"
    os.execl(git_shell_cmd, git_shell_cmd, '-c', cmd)
elif action == 'set-keywords':
    if len(cmdargv) < 2:
        die_with_help("{:s}: missing repository name".format(action))
    pkgbase_set_keywords(cmdargv[1], cmdargv[2:])
elif action == 'list-repos':
    if len(cmdargv) > 1:
        die_with_help("{:s}: too many arguments".format(action))
    list_repos(user)
elif action == 'setup-repo':
    if len(cmdargv) < 2:
        die_with_help("{:s}: missing repository name".format(action))
    if len(cmdargv) > 2:
        die_with_help("{:s}: too many arguments".format(action))
    create_pkgbase(cmdargv[1], user)
elif action == 'restore':
    if len(cmdargv) < 2:
        die_with_help("{:s}: missing repository name".format(action))
    if len(cmdargv) > 2:
        die_with_help("{:s}: too many arguments".format(action))

    pkgbase = cmdargv[1]
    if not re.match(repo_regex, pkgbase):
        die('{:s}: invalid repository name: {:s}'.format(action, pkgbase))

    if pkgbase_exists(pkgbase):
        die('{:s}: package base exists: {:s}'.format(action, pkgbase))
    create_pkgbase(pkgbase, user)

    os.environ["AUR_USER"] = user
    os.environ["AUR_PKGBASE"] = pkgbase
    os.execl(git_update_cmd, git_update_cmd, 'restore')
elif action == 'help':
    die("Commands:\n" +
        "  help                         Show this help message and exit.\n" +
        "  list-repos                   List all your repositories.\n" +
        "  restore <name>               Restore a deleted package base.\n" +
        "  set-keywords <name> [...]    Change package base keywords.\n" +
        "  setup-repo <name>            Create an empty repository.\n" +
        "  git-receive-pack             Internal command used with Git.\n" +
        "  git-upload-pack              Internal command used with Git.")
else:
    die_with_help("invalid command: {:s}".format(action))
