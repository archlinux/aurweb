"""Common logic for both legacy and new git update hook."""

import subprocess
import sys
import time

import pygit2

import aurweb.config

notify_cmd = aurweb.config.get("notifications", "notify-cmd")

max_blob_size = aurweb.config.getint("update", "max-blob-size")


def size_humanize(num):
    for unit in ["B", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB", "ZiB"]:
        if abs(num) < 2048.0:
            if isinstance(num, int):
                return f"{num}{unit}"
            else:
                return f"{num:.2f}{unit}"
        num /= 1024.0
    return "{:.2f}{}".format(num, "YiB")


def ref_commit_times(repo, sha1):
    walker = repo.walk(sha1, pygit2.GIT_SORT_TOPOLOGICAL | pygit2.GIT_SORT_REVERSE)
    first = next(iter(walker)).commit_time
    return first, repo.get(sha1).commit_time


def create_pkgbase(conn, pkgbase, user, orphan=False, submitted_ts=None):
    cur = conn.execute("SELECT ID FROM Users WHERE Username = ?", [user])
    userid = cur.fetchone()[0]

    owner = None if orphan else userid

    submitted = int(time.time()) if submitted_ts is None else submitted_ts
    cur = conn.execute(
        "INSERT INTO PackageBases (Name, SubmittedTS, "
        + "ModifiedTS, SubmitterUID, MaintainerUID, "
        + "FlaggerComment) VALUES (?, ?, ?, ?, ?, '')",
        [pkgbase, submitted, submitted, owner, owner],
    )
    pkgbase_id = cur.lastrowid

    cur = conn.execute(
        "INSERT INTO PackageNotifications " + "(PackageBaseID, UserID) VALUES (?, ?)",
        [pkgbase_id, userid],
    )

    conn.commit()

    return pkgbase_id


def claim_orphan_if_comaintainer(conn, pkgbase_id, user_id):
    conn.execute(
        "UPDATE PackageBases SET MaintainerUID = ? "
        + "WHERE ID = ? AND MaintainerUID IS NULL AND EXISTS ("
        + "SELECT 1 FROM PackageComaintainers "
        + "WHERE PackageBaseID = ? AND UsersID = ?)",
        [user_id, pkgbase_id, pkgbase_id, user_id],
    )


def deleted_pkgbase_msg(pkgbase):
    ssh_cmdline = aurweb.config.get("serve", "ssh-cmdline")
    return (
        f"{pkgbase:s} was deleted; pushing does not restore it. Run "
        f"`{ssh_cmdline:s} restore {pkgbase:s}` to bring it back as an orphan, "
        f"then `{ssh_cmdline:s} adopt {pkgbase:s}` to request maintainership."
    )


def update_notify(conn, user, pkgbase_id):
    # Obtain the user ID of the new maintainer.
    cur = conn.execute("SELECT ID FROM Users WHERE Username = ?", [user])
    user_id = int(cur.fetchone()[0])

    # Execute the notification script.
    subprocess.run((notify_cmd, "update", str(user_id), str(pkgbase_id)))


def die(msg):
    sys.stderr.write(f"error: {msg:s}\n")
    exit(1)


def warn(msg):
    sys.stderr.write(f"warning: {msg:s}\n")


def die_commit(msg, commit):
    sys.stderr.write("error: The following error " + "occurred when parsing commit\n")
    sys.stderr.write(f"error: {commit:s}:\n")
    sys.stderr.write(f"error: {msg:s}\n")
    exit(1)


def validate_blob_size(blob: pygit2.Object, commit: pygit2.Commit):
    if isinstance(blob, pygit2.Blob) and blob.size > max_blob_size:
        die_commit(
            f"maximum blob size ({size_humanize(max_blob_size):s}) exceeded",
            str(commit.id),
        )
