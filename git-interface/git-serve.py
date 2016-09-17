#!/usr/bin/python3

import os
import re
import shlex
import subprocess
import sys
import time

import config
import db

notify_cmd = config.get('notifications', 'notify-cmd')

repo_path = config.get('serve', 'repo-path')
repo_regex = config.get('serve', 'repo-regex')
git_shell_cmd = config.get('serve', 'git-shell-cmd')
git_update_cmd = config.get('serve', 'git-update-cmd')
ssh_cmdline = config.get('serve', 'ssh-cmdline')

enable_maintenance = config.getboolean('options', 'enable-maintenance')
maintenance_exc = config.get('options', 'maintenance-exceptions').split()


def pkgbase_from_name(pkgbase):
    conn = db.Connection()
    cur = conn.execute("SELECT ID FROM PackageBases WHERE Name = ?", [pkgbase])

    row = cur.fetchone()
    return row[0] if row else None


def pkgbase_exists(pkgbase):
    return pkgbase_from_name(pkgbase) is not None


def list_repos(user):
    conn = db.Connection()

    cur = conn.execute("SELECT ID FROM Users WHERE Username = ?", [user])
    userid = cur.fetchone()[0]
    if userid == 0:
        die('{:s}: unknown user: {:s}'.format(action, user))

    cur = conn.execute("SELECT Name, PackagerUID FROM PackageBases " +
                       "WHERE MaintainerUID = ?", [userid])
    for row in cur:
        print((' ' if row[1] else '*') + row[0])
    conn.close()


def create_pkgbase(pkgbase, user):
    if not re.match(repo_regex, pkgbase):
        die('{:s}: invalid repository name: {:s}'.format(action, pkgbase))
    if pkgbase_exists(pkgbase):
        die('{:s}: package base already exists: {:s}'.format(action, pkgbase))

    conn = db.Connection()

    cur = conn.execute("SELECT ID FROM Users WHERE Username = ?", [user])
    userid = cur.fetchone()[0]
    if userid == 0:
        die('{:s}: unknown user: {:s}'.format(action, user))

    now = int(time.time())
    cur = conn.execute("INSERT INTO PackageBases (Name, SubmittedTS, " +
                       "ModifiedTS, SubmitterUID, MaintainerUID) VALUES " +
                       "(?, ?, ?, ?, ?)", [pkgbase, now, now, userid, userid])
    pkgbase_id = cur.lastrowid

    cur = conn.execute("INSERT INTO PackageNotifications " +
                       "(PackageBaseID, UserID) VALUES (?, ?)",
                       [pkgbase_id, userid])

    conn.commit()
    conn.close()


def pkgbase_adopt(pkgbase):
    pkgbase_id = pkgbase_from_name(pkgbase)
    if not pkgbase_id:
        die('{:s}: package base not found: {:s}'.format(action, pkgbase))

    conn = db.Connection()

    cur = conn.execute("SELECT ID FROM PackageBases WHERE ID = ? AND " +
                       "MaintainerUID IS NULL", [pkgbase_id])
    if not privileged and not cur.fetchone():
        die('{:s}: permission denied: {:s}'.format(action, user))

    cur = conn.execute("SELECT ID FROM Users WHERE Username = ?", [user])
    userid = cur.fetchone()[0]
    if userid == 0:
        die('{:s}: unknown user: {:s}'.format(action, user))

    cur = conn.execute("UPDATE PackageBases SET MaintainerUID = ? " +
                       "WHERE ID = ?", [userid, pkgbase_id])

    cur = conn.execute("SELECT COUNT(*) FROM PackageNotifications WHERE " +
                       "PackageBaseID = ? AND UserID = ?",
                       [pkgbase_id, userid])
    if cur.fetchone()[0] == 0:
        cur = conn.execute("INSERT INTO PackageNotifications " +
                           "(PackageBaseID, UserID) VALUES (?, ?)",
                           [pkgbase_id, userid])
    conn.commit()

    subprocess.Popen((notify_cmd, 'adopt', str(pkgbase_id), str(userid)))

    conn.close()


def pkgbase_get_comaintainers(pkgbase):
    conn = db.Connection()

    cur = conn.execute("SELECT UserName FROM PackageComaintainers " +
                       "INNER JOIN Users " +
                       "ON Users.ID = PackageComaintainers.UsersID " +
                       "INNER JOIN PackageBases " +
                       "ON PackageBases.ID = PackageComaintainers.PackageBaseID " +
                       "WHERE PackageBases.Name = ? " +
                       "ORDER BY Priority ASC", [pkgbase])

    return [row[0] for row in cur.fetchall()]


def pkgbase_set_comaintainers(pkgbase, userlist):
    pkgbase_id = pkgbase_from_name(pkgbase)
    if not pkgbase_id:
        die('{:s}: package base not found: {:s}'.format(action, pkgbase))

    if not privileged and not pkgbase_has_full_access(pkgbase, user):
        die('{:s}: permission denied: {:s}'.format(action, user))

    conn = db.Connection()

    userlist_old = set(pkgbase_get_comaintainers(pkgbase))

    uids_old = set()
    for olduser in userlist_old:
        cur = conn.execute("SELECT ID FROM Users WHERE Username = ?",
                           [olduser])
        userid = cur.fetchone()[0]
        if userid == 0:
            die('{:s}: unknown user: {:s}'.format(action, user))
        uids_old.add(userid)

    uids_new = set()
    for newuser in userlist:
        cur = conn.execute("SELECT ID FROM Users WHERE Username = ?",
                           [newuser])
        userid = cur.fetchone()[0]
        if userid == 0:
            die('{:s}: unknown user: {:s}'.format(action, user))
        uids_new.add(userid)

    uids_add = uids_new - uids_old
    uids_rem = uids_old - uids_new

    i = 1
    for userid in uids_new:
        if userid in uids_add:
            cur = conn.execute("INSERT INTO PackageComaintainers " +
                               "(PackageBaseID, UsersID, Priority) " +
                               "VALUES (?, ?, ?)", [pkgbase_id, userid, i])
            subprocess.Popen((notify_cmd, 'comaintainer-add', str(pkgbase_id),
                              str(userid)))
        else:
            cur = conn.execute("UPDATE PackageComaintainers " +
                               "SET Priority = ? " +
                               "WHERE PackageBaseID = ? AND UsersID = ?",
                               [i, pkgbase_id, userid])
        i += 1

    for userid in uids_rem:
            cur = conn.execute("DELETE FROM PackageComaintainers " +
                               "WHERE PackageBaseID = ? AND UsersID = ?",
                               [pkgbase_id, userid])
            subprocess.Popen((notify_cmd, 'comaintainer-remove',
                              str(pkgbase_id), str(userid)))

    conn.commit()
    conn.close()


def pkgbase_disown(pkgbase):
    pkgbase_id = pkgbase_from_name(pkgbase)
    if not pkgbase_id:
        die('{:s}: package base not found: {:s}'.format(action, pkgbase))

    initialized_by_owner = pkgbase_has_full_access(pkgbase, user)
    if not privileged and not initialized_by_owner:
        die('{:s}: permission denied: {:s}'.format(action, user))

    # TODO: Support disowning package bases via package request.
    # TODO: Scan through pending orphan requests and close them.

    comaintainers = []
    new_maintainer_userid = None

    conn = db.Connection()

    # Make the first co-maintainer the new maintainer, unless the action was
    # enforced by a Trusted User.
    if initialized_by_owner:
        comaintainers = pkgbase_get_comaintainers(pkgbase)
        if len(comaintainers) > 0:
            new_maintainer = comaintainers[0]
            cur = conn.execute("SELECT ID FROM Users WHERE Username = ?",
                               [new_maintainer])
            new_maintainer_userid = cur.fetchone()[0]
            comaintainers.remove(new_maintainer)

    pkgbase_set_comaintainers(pkgbase, comaintainers)
    cur = conn.execute("UPDATE PackageBases SET MaintainerUID = ? " +
                       "WHERE ID = ?", [new_maintainer_userid, pkgbase_id])

    conn.commit()

    cur = conn.execute("SELECT ID FROM Users WHERE Username = ?", [user])
    userid = cur.fetchone()[0]
    if userid == 0:
        die('{:s}: unknown user: {:s}'.format(action, user))

    subprocess.Popen((notify_cmd, 'disown', str(pkgbase_id), str(userid)))

    conn.close()


def pkgbase_set_keywords(pkgbase, keywords):
    pkgbase_id = pkgbase_from_name(pkgbase)
    if not pkgbase_id:
        die('{:s}: package base not found: {:s}'.format(action, pkgbase))

    conn = db.Connection()

    conn.execute("DELETE FROM PackageKeywords WHERE PackageBaseID = ?",
                 [pkgbase_id])
    for keyword in keywords:
        conn.execute("INSERT INTO PackageKeywords (PackageBaseID, Keyword) " +
                     "VALUES (?, ?)", [pkgbase_id, keyword])

    conn.commit()
    conn.close()


def pkgbase_has_write_access(pkgbase, user):
    conn = db.Connection()

    cur = conn.execute("SELECT COUNT(*) FROM PackageBases " +
                       "LEFT JOIN PackageComaintainers " +
                       "ON PackageComaintainers.PackageBaseID = PackageBases.ID " +
                       "INNER JOIN Users " +
                       "ON Users.ID = PackageBases.MaintainerUID " +
                       "OR PackageBases.MaintainerUID IS NULL " +
                       "OR Users.ID = PackageComaintainers.UsersID " +
                       "WHERE Name = ? AND Username = ?", [pkgbase, user])
    return cur.fetchone()[0] > 0


def pkgbase_has_full_access(pkgbase, user):
    conn = db.Connection()

    cur = conn.execute("SELECT COUNT(*) FROM PackageBases " +
                       "INNER JOIN Users " +
                       "ON Users.ID = PackageBases.MaintainerUID " +
                       "WHERE Name = ? AND Username = ?", [pkgbase, user])
    return cur.fetchone()[0] > 0


def die(msg):
    sys.stderr.write("{:s}\n".format(msg))
    exit(1)


def die_with_help(msg):
    die(msg + "\nTry `{:s} help` for a list of commands.".format(ssh_cmdline))


def warn(msg):
    sys.stderr.write("warning: {:s}\n".format(msg))


def usage(cmds):
    sys.stderr.write("Commands:\n")
    colwidth = max([len(cmd) for cmd in cmds.keys()]) + 4
    for key in sorted(cmds):
        sys.stderr.write("  " + key.ljust(colwidth) + cmds[key] + "\n")
    exit(0)


user = os.environ.get('AUR_USER')
privileged = (os.environ.get('AUR_PRIVILEGED', '0') == '1')
ssh_cmd = os.environ.get('SSH_ORIGINAL_COMMAND')
ssh_client = os.environ.get('SSH_CLIENT')

if not ssh_cmd:
    die_with_help("Interactive shell is disabled.")
cmdargv = shlex.split(ssh_cmd)
action = cmdargv[0]
remote_addr = ssh_client.split(' ')[0] if ssh_client else None

if enable_maintenance:
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

    if action == 'git-receive-pack' and pkgbase_exists(pkgbase):
        if not privileged and not pkgbase_has_write_access(pkgbase, user):
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
    warn('{:s} is deprecated. Use `git push` to create new repositories.'.format(action))
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
elif action == 'adopt':
    if len(cmdargv) < 2:
        die_with_help("{:s}: missing repository name".format(action))
    if len(cmdargv) > 2:
        die_with_help("{:s}: too many arguments".format(action))

    pkgbase = cmdargv[1]
    pkgbase_adopt(pkgbase)
elif action == 'disown':
    if len(cmdargv) < 2:
        die_with_help("{:s}: missing repository name".format(action))
    if len(cmdargv) > 2:
        die_with_help("{:s}: too many arguments".format(action))

    pkgbase = cmdargv[1]
    pkgbase_disown(pkgbase)
elif action == 'set-comaintainers':
    if len(cmdargv) < 2:
        die_with_help("{:s}: missing repository name".format(action))

    pkgbase = cmdargv[1]
    userlist = cmdargv[2:]
    pkgbase_set_comaintainers(pkgbase, userlist)
elif action == 'help':
    cmds = {
        "adopt <name>": "Adopt a package base.",
        "disown <name>": "Disown a package base.",
        "help": "Show this help message and exit.",
        "list-repos": "List all your repositories.",
        "restore <name>": "Restore a deleted package base.",
        "set-comaintainers <name> [...]": "Set package base co-maintainers.",
        "set-keywords <name> [...]": "Change package base keywords.",
        "setup-repo <name>": "Create a repository (deprecated).",
        "git-receive-pack": "Internal command used with Git.",
        "git-upload-pack": "Internal command used with Git.",
    }
    usage(cmds)
else:
    die_with_help("invalid command: {:s}".format(action))
