#!/usr/bin/env python3

import os
import re
import shlex
import subprocess
import sys
import time

import aurweb.config
import aurweb.db
import aurweb.exceptions

notify_cmd = aurweb.config.get('notifications', 'notify-cmd')

repo_path = aurweb.config.get('serve', 'repo-path')
repo_regex = aurweb.config.get('serve', 'repo-regex')
git_shell_cmd = aurweb.config.get('serve', 'git-shell-cmd')
git_update_cmd = aurweb.config.get('serve', 'git-update-cmd')
ssh_cmdline = aurweb.config.get('serve', 'ssh-cmdline')

enable_maintenance = aurweb.config.getboolean('options', 'enable-maintenance')
maintenance_exc = aurweb.config.get('options', 'maintenance-exceptions').split()


def pkgbase_from_name(pkgbase):
    conn = aurweb.db.Connection()
    cur = conn.execute("SELECT ID FROM PackageBases WHERE Name = ?", [pkgbase])

    row = cur.fetchone()
    return row[0] if row else None


def pkgbase_exists(pkgbase):
    return pkgbase_from_name(pkgbase) is not None


def list_repos(user):
    conn = aurweb.db.Connection()

    cur = conn.execute("SELECT ID FROM Users WHERE Username = ?", [user])
    userid = cur.fetchone()[0]
    if userid == 0:
        raise aurweb.exceptions.InvalidUserException(user)

    cur = conn.execute("SELECT Name, PackagerUID FROM PackageBases " +
                       "WHERE MaintainerUID = ?", [userid])
    for row in cur:
        print((' ' if row[1] else '*') + row[0])
    conn.close()


def create_pkgbase(pkgbase, user):
    if not re.match(repo_regex, pkgbase):
        raise aurweb.exceptions.InvalidRepositoryNameException(pkgbase)
    if pkgbase_exists(pkgbase):
        raise aurweb.exceptions.PackageBaseExistsException(pkgbase)

    conn = aurweb.db.Connection()

    cur = conn.execute("SELECT ID FROM Users WHERE Username = ?", [user])
    userid = cur.fetchone()[0]
    if userid == 0:
        raise aurweb.exceptions.InvalidUserException(user)

    now = int(time.time())
    cur = conn.execute("INSERT INTO PackageBases (Name, SubmittedTS, " +
                       "ModifiedTS, SubmitterUID, MaintainerUID, " +
                       "FlaggerComment) VALUES (?, ?, ?, ?, ?, '')",
                       [pkgbase, now, now, userid, userid])
    pkgbase_id = cur.lastrowid

    cur = conn.execute("INSERT INTO PackageNotifications " +
                       "(PackageBaseID, UserID) VALUES (?, ?)",
                       [pkgbase_id, userid])

    conn.commit()
    conn.close()


def pkgbase_adopt(pkgbase, user, privileged):
    pkgbase_id = pkgbase_from_name(pkgbase)
    if not pkgbase_id:
        raise aurweb.exceptions.InvalidPackageBaseException(pkgbase)

    conn = aurweb.db.Connection()

    cur = conn.execute("SELECT ID FROM PackageBases WHERE ID = ? AND " +
                       "MaintainerUID IS NULL", [pkgbase_id])
    if not privileged and not cur.fetchone():
        raise aurweb.exceptions.PermissionDeniedException(user)

    cur = conn.execute("SELECT ID FROM Users WHERE Username = ?", [user])
    userid = cur.fetchone()[0]
    if userid == 0:
        raise aurweb.exceptions.InvalidUserException(user)

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

    subprocess.Popen((notify_cmd, 'adopt', str(userid), str(pkgbase_id)))

    conn.close()


def pkgbase_get_comaintainers(pkgbase):
    conn = aurweb.db.Connection()

    cur = conn.execute("SELECT UserName FROM PackageComaintainers " +
                       "INNER JOIN Users " +
                       "ON Users.ID = PackageComaintainers.UsersID " +
                       "INNER JOIN PackageBases " +
                       "ON PackageBases.ID = PackageComaintainers.PackageBaseID " +
                       "WHERE PackageBases.Name = ? " +
                       "ORDER BY Priority ASC", [pkgbase])

    return [row[0] for row in cur.fetchall()]


def pkgbase_set_comaintainers(pkgbase, userlist, user, privileged):
    pkgbase_id = pkgbase_from_name(pkgbase)
    if not pkgbase_id:
        raise aurweb.exceptions.InvalidPackageBaseException(pkgbase)

    if not privileged and not pkgbase_has_full_access(pkgbase, user):
        raise aurweb.exceptions.PermissionDeniedException(user)

    conn = aurweb.db.Connection()

    userlist_old = set(pkgbase_get_comaintainers(pkgbase))

    uids_old = set()
    for olduser in userlist_old:
        cur = conn.execute("SELECT ID FROM Users WHERE Username = ?",
                           [olduser])
        userid = cur.fetchone()[0]
        if userid == 0:
            raise aurweb.exceptions.InvalidUserException(user)
        uids_old.add(userid)

    uids_new = set()
    for newuser in userlist:
        cur = conn.execute("SELECT ID FROM Users WHERE Username = ?",
                           [newuser])
        userid = cur.fetchone()[0]
        if userid == 0:
            raise aurweb.exceptions.InvalidUserException(user)
        uids_new.add(userid)

    uids_add = uids_new - uids_old
    uids_rem = uids_old - uids_new

    i = 1
    for userid in uids_new:
        if userid in uids_add:
            cur = conn.execute("INSERT INTO PackageComaintainers " +
                               "(PackageBaseID, UsersID, Priority) " +
                               "VALUES (?, ?, ?)", [pkgbase_id, userid, i])
            subprocess.Popen((notify_cmd, 'comaintainer-add', str(userid),
                              str(pkgbase_id)))
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
                              str(userid), str(pkgbase_id)))

    conn.commit()
    conn.close()


def pkgreq_by_pkgbase(pkgbase_id, reqtype):
    conn = aurweb.db.Connection()

    cur = conn.execute("SELECT PackageRequests.ID FROM PackageRequests " +
                       "INNER JOIN RequestTypes ON " +
                       "RequestTypes.ID = PackageRequests.ReqTypeID " +
                       "WHERE PackageRequests.Status = 0 " +
                       "AND PackageRequests.PackageBaseID = ? " +
                       "AND RequestTypes.Name = ?", [pkgbase_id, reqtype])

    return [row[0] for row in cur.fetchall()]


def pkgreq_close(reqid, user, reason, comments, autoclose=False):
    statusmap = {'accepted': 2, 'rejected': 3}
    if reason not in statusmap:
        raise aurweb.exceptions.InvalidReasonException(reason)
    status = statusmap[reason]

    conn = aurweb.db.Connection()

    if autoclose:
        userid = 0
    else:
        cur = conn.execute("SELECT ID FROM Users WHERE Username = ?", [user])
        userid = cur.fetchone()[0]
        if userid == 0:
            raise aurweb.exceptions.InvalidUserException(user)

    conn.execute("UPDATE PackageRequests SET Status = ?, ClosureComment = ? " +
                 "WHERE ID = ?", [status, comments, reqid])
    conn.commit()
    conn.close()

    subprocess.Popen((notify_cmd, 'request-close', str(userid), str(reqid),
                      reason)).wait()


def pkgbase_disown(pkgbase, user, privileged):
    pkgbase_id = pkgbase_from_name(pkgbase)
    if not pkgbase_id:
        raise aurweb.exceptions.InvalidPackageBaseException(pkgbase)

    initialized_by_owner = pkgbase_has_full_access(pkgbase, user)
    if not privileged and not initialized_by_owner:
        raise aurweb.exceptions.PermissionDeniedException(user)

    # TODO: Support disowning package bases via package request.

    # Scan through pending orphan requests and close them.
    comment = 'The user {:s} disowned the package.'.format(user)
    for reqid in pkgreq_by_pkgbase(pkgbase_id, 'orphan'):
        pkgreq_close(reqid, user, 'accepted', comment, True)

    comaintainers = []
    new_maintainer_userid = None

    conn = aurweb.db.Connection()

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

    pkgbase_set_comaintainers(pkgbase, comaintainers, user, privileged)
    cur = conn.execute("UPDATE PackageBases SET MaintainerUID = ? " +
                       "WHERE ID = ?", [new_maintainer_userid, pkgbase_id])

    conn.commit()

    cur = conn.execute("SELECT ID FROM Users WHERE Username = ?", [user])
    userid = cur.fetchone()[0]
    if userid == 0:
            raise aurweb.exceptions.InvalidUserException(user)

    subprocess.Popen((notify_cmd, 'disown', str(userid), str(pkgbase_id)))

    conn.close()


def pkgbase_flag(pkgbase, user, comment):
    pkgbase_id = pkgbase_from_name(pkgbase)
    if not pkgbase_id:
        raise aurweb.exceptions.InvalidPackageBaseException(pkgbase)
    if len(comment) < 3:
        raise aurweb.exceptions.InvalidCommentException(comment)

    conn = aurweb.db.Connection()

    cur = conn.execute("SELECT ID FROM Users WHERE Username = ?", [user])
    userid = cur.fetchone()[0]
    if userid == 0:
        raise aurweb.exceptions.InvalidUserException(user)

    now = int(time.time())
    conn.execute("UPDATE PackageBases SET " +
                 "OutOfDateTS = ?, FlaggerUID = ?, FlaggerComment = ? " +
                 "WHERE ID = ? AND OutOfDateTS IS NULL",
                 [now, userid, comment, pkgbase_id])

    conn.commit()

    subprocess.Popen((notify_cmd, 'flag', str(userid), str(pkgbase_id)))


def pkgbase_unflag(pkgbase, user):
    pkgbase_id = pkgbase_from_name(pkgbase)
    if not pkgbase_id:
        raise aurweb.exceptions.InvalidPackageBaseException(pkgbase)

    conn = aurweb.db.Connection()

    cur = conn.execute("SELECT ID FROM Users WHERE Username = ?", [user])
    userid = cur.fetchone()[0]
    if userid == 0:
        raise aurweb.exceptions.InvalidUserException(user)

    if user in pkgbase_get_comaintainers(pkgbase):
        conn.execute("UPDATE PackageBases SET OutOfDateTS = NULL " +
                     "WHERE ID = ?", [pkgbase_id])
    else:
        conn.execute("UPDATE PackageBases SET OutOfDateTS = NULL " +
                     "WHERE ID = ? AND (MaintainerUID = ? OR FlaggerUID = ?)",
                     [pkgbase_id, userid, userid])

    conn.commit()


def pkgbase_vote(pkgbase, user):
    pkgbase_id = pkgbase_from_name(pkgbase)
    if not pkgbase_id:
        raise aurweb.exceptions.InvalidPackageBaseException(pkgbase)

    conn = aurweb.db.Connection()

    cur = conn.execute("SELECT ID FROM Users WHERE Username = ?", [user])
    userid = cur.fetchone()[0]
    if userid == 0:
        raise aurweb.exceptions.InvalidUserException(user)

    cur = conn.execute("SELECT COUNT(*) FROM PackageVotes " +
                       "WHERE UsersID = ? AND PackageBaseID = ?",
                       [userid, pkgbase_id])
    if cur.fetchone()[0] > 0:
        raise aurweb.exceptions.AlreadyVotedException(pkgbase)

    now = int(time.time())
    conn.execute("INSERT INTO PackageVotes (UsersID, PackageBaseID, VoteTS) " +
                 "VALUES (?, ?, ?)", [userid, pkgbase_id, now])
    conn.execute("UPDATE PackageBases SET NumVotes = NumVotes + 1 " +
                 "WHERE ID = ?", [pkgbase_id])
    conn.commit()


def pkgbase_unvote(pkgbase, user):
    pkgbase_id = pkgbase_from_name(pkgbase)
    if not pkgbase_id:
        raise aurweb.exceptions.InvalidPackageBaseException(pkgbase)

    conn = aurweb.db.Connection()

    cur = conn.execute("SELECT ID FROM Users WHERE Username = ?", [user])
    userid = cur.fetchone()[0]
    if userid == 0:
        raise aurweb.exceptions.InvalidUserException(user)

    cur = conn.execute("SELECT COUNT(*) FROM PackageVotes " +
                       "WHERE UsersID = ? AND PackageBaseID = ?",
                       [userid, pkgbase_id])
    if cur.fetchone()[0] == 0:
        raise aurweb.exceptions.NotVotedException(pkgbase)

    conn.execute("DELETE FROM PackageVotes WHERE UsersID = ? AND " +
                 "PackageBaseID = ?", [userid, pkgbase_id])
    conn.execute("UPDATE PackageBases SET NumVotes = NumVotes - 1 " +
                 "WHERE ID = ?", [pkgbase_id])
    conn.commit()


def pkgbase_set_keywords(pkgbase, keywords):
    pkgbase_id = pkgbase_from_name(pkgbase)
    if not pkgbase_id:
        raise aurweb.exceptions.InvalidPackageBaseException(pkgbase)

    conn = aurweb.db.Connection()

    conn.execute("DELETE FROM PackageKeywords WHERE PackageBaseID = ?",
                 [pkgbase_id])
    for keyword in keywords:
        conn.execute("INSERT INTO PackageKeywords (PackageBaseID, Keyword) " +
                     "VALUES (?, ?)", [pkgbase_id, keyword])

    conn.commit()
    conn.close()


def pkgbase_has_write_access(pkgbase, user):
    conn = aurweb.db.Connection()

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
    conn = aurweb.db.Connection()

    cur = conn.execute("SELECT COUNT(*) FROM PackageBases " +
                       "INNER JOIN Users " +
                       "ON Users.ID = PackageBases.MaintainerUID " +
                       "WHERE Name = ? AND Username = ?", [pkgbase, user])
    return cur.fetchone()[0] > 0


def log_ssh_login(user, remote_addr):
    conn = aurweb.db.Connection()

    now = int(time.time())
    conn.execute("UPDATE Users SET LastSSHLogin = ?, " +
                 "LastSSHLoginIPAddress = ? WHERE Username = ?",
                 [now, remote_addr, user])

    conn.commit()
    conn.close()


def bans_match(remote_addr):
    conn = aurweb.db.Connection()

    cur = conn.execute("SELECT COUNT(*) FROM Bans WHERE IPAddress = ?",
                       [remote_addr])
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


def checkarg_atleast(cmdargv, *argdesc):
    if len(cmdargv) - 1 < len(argdesc):
        msg = 'missing {:s}'.format(argdesc[len(cmdargv) - 1])
        raise aurweb.exceptions.InvalidArgumentsException(msg)


def checkarg_atmost(cmdargv, *argdesc):
    if len(cmdargv) - 1 > len(argdesc):
        raise aurweb.exceptions.InvalidArgumentsException('too many arguments')


def checkarg(cmdargv, *argdesc):
    checkarg_atleast(cmdargv, *argdesc)
    checkarg_atmost(cmdargv, *argdesc)


def serve(action, cmdargv, user, privileged, remote_addr):
    if enable_maintenance:
        if remote_addr not in maintenance_exc:
            raise aurweb.exceptions.MaintenanceException
    if bans_match(remote_addr):
        raise aurweb.exceptions.BannedException
    log_ssh_login(user, remote_addr)

    if action == 'git' and cmdargv[1] in ('upload-pack', 'receive-pack'):
        action = action + '-' + cmdargv[1]
        del cmdargv[1]

    if action == 'git-upload-pack' or action == 'git-receive-pack':
        checkarg(cmdargv, 'path')

        path = cmdargv[1].rstrip('/')
        if not path.startswith('/'):
            path = '/' + path
        if not path.endswith('.git'):
            path = path + '.git'
        pkgbase = path[1:-4]
        if not re.match(repo_regex, pkgbase):
            raise aurweb.exceptions.InvalidRepositoryNameException(pkgbase)

        if action == 'git-receive-pack' and pkgbase_exists(pkgbase):
            if not privileged and not pkgbase_has_write_access(pkgbase, user):
                raise aurweb.exceptions.PermissionDeniedException(user)

        os.environ["AUR_USER"] = user
        os.environ["AUR_PKGBASE"] = pkgbase
        os.environ["GIT_NAMESPACE"] = pkgbase
        cmd = action + " '" + repo_path + "'"
        os.execl(git_shell_cmd, git_shell_cmd, '-c', cmd)
    elif action == 'set-keywords':
        checkarg_atleast(cmdargv, 'repository name')
        pkgbase_set_keywords(cmdargv[1], cmdargv[2:])
    elif action == 'list-repos':
        checkarg(cmdargv)
        list_repos(user)
    elif action == 'setup-repo':
        checkarg(cmdargv, 'repository name')
        warn('{:s} is deprecated. '
             'Use `git push` to create new repositories.'.format(action))
        create_pkgbase(cmdargv[1], user)
    elif action == 'restore':
        checkarg(cmdargv, 'repository name')

        pkgbase = cmdargv[1]
        create_pkgbase(pkgbase, user)

        os.environ["AUR_USER"] = user
        os.environ["AUR_PKGBASE"] = pkgbase
        os.execl(git_update_cmd, git_update_cmd, 'restore')
    elif action == 'adopt':
        checkarg(cmdargv, 'repository name')

        pkgbase = cmdargv[1]
        pkgbase_adopt(pkgbase, user, privileged)
    elif action == 'disown':
        checkarg(cmdargv, 'repository name')

        pkgbase = cmdargv[1]
        pkgbase_disown(pkgbase, user, privileged)
    elif action == 'flag':
        checkarg(cmdargv, 'repository name', 'comment')

        pkgbase = cmdargv[1]
        comment = cmdargv[2]
        pkgbase_flag(pkgbase, user, comment)
    elif action == 'unflag':
        checkarg(cmdargv, 'repository name')

        pkgbase = cmdargv[1]
        pkgbase_unflag(pkgbase, user)
    elif action == 'vote':
        checkarg(cmdargv, 'repository name')

        pkgbase = cmdargv[1]
        pkgbase_vote(pkgbase, user)
    elif action == 'unvote':
        checkarg(cmdargv, 'repository name')

        pkgbase = cmdargv[1]
        pkgbase_unvote(pkgbase, user)
    elif action == 'set-comaintainers':
        checkarg_atleast(cmdargv, 'repository name')

        pkgbase = cmdargv[1]
        userlist = cmdargv[2:]
        pkgbase_set_comaintainers(pkgbase, userlist, user, privileged)
    elif action == 'help':
        cmds = {
            "adopt <name>": "Adopt a package base.",
            "disown <name>": "Disown a package base.",
            "flag <name> <comment>": "Flag a package base out-of-date.",
            "help": "Show this help message and exit.",
            "list-repos": "List all your repositories.",
            "restore <name>": "Restore a deleted package base.",
            "set-comaintainers <name> [...]": "Set package base co-maintainers.",
            "set-keywords <name> [...]": "Change package base keywords.",
            "setup-repo <name>": "Create a repository (deprecated).",
            "unflag <name>": "Remove out-of-date flag from a package base.",
            "unvote <name>": "Remove vote from a package base.",
            "vote <name>": "Vote for a package base.",
            "git-receive-pack": "Internal command used with Git.",
            "git-upload-pack": "Internal command used with Git.",
        }
        usage(cmds)
    else:
        msg = 'invalid command: {:s}'.format(action)
        raise aurweb.exceptions.InvalidArgumentsException(msg)


def main():
    user = os.environ.get('AUR_USER')
    privileged = (os.environ.get('AUR_PRIVILEGED', '0') == '1')
    ssh_cmd = os.environ.get('SSH_ORIGINAL_COMMAND')
    ssh_client = os.environ.get('SSH_CLIENT')

    if not ssh_cmd:
        die_with_help("Interactive shell is disabled.")
    cmdargv = shlex.split(ssh_cmd)
    action = cmdargv[0]
    remote_addr = ssh_client.split(' ')[0] if ssh_client else None

    try:
        serve(action, cmdargv, user, privileged, remote_addr)
    except aurweb.exceptions.MaintenanceException:
        die("The AUR is down due to maintenance. We will be back soon.")
    except aurweb.exceptions.BannedException:
        die("The SSH interface is disabled for your IP address.")
    except aurweb.exceptions.InvalidArgumentsException as e:
        die_with_help('{:s}: {}'.format(action, e))
    except aurweb.exceptions.AurwebException as e:
        die('{:s}: {}'.format(action, e))


if __name__ == '__main__':
    main()
