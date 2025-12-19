"""Common logic for both legacy and new git update hook."""

import subprocess
import sys
import time

import pygit2

import aurweb.config

notify_cmd = aurweb.config.get("notifications", "notify-cmd")

max_blob_size = aurweb.config.getint("update", "max-blob-size")

allowed_license_file_exts = ("md", "txt")


def size_humanize(num):
    for unit in ["B", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB", "ZiB"]:
        if abs(num) < 2048.0:
            if isinstance(num, int):
                return f"{num}{unit}"
            else:
                return f"{num:.2f}{unit}"
        num /= 1024.0
    return "{:.2f}{}".format(num, "YiB")


def create_pkgbase(conn, pkgbase, user):
    cur = conn.execute("SELECT ID FROM Users WHERE Username = ?", [user])
    userid = cur.fetchone()[0]

    now = int(time.time())
    cur = conn.execute(
        "INSERT INTO PackageBases (Name, SubmittedTS, "
        + "ModifiedTS, SubmitterUID, MaintainerUID, "
        + "FlaggerComment) VALUES (?, ?, ?, ?, ?, '')",
        [pkgbase, now, now, userid, userid],
    )
    pkgbase_id = cur.lastrowid

    cur = conn.execute(
        "INSERT INTO PackageNotifications " + "(PackageBaseID, UserID) VALUES (?, ?)",
        [pkgbase_id, userid],
    )

    conn.commit()

    return pkgbase_id


def update_notify(conn, user, pkgbase_id):
    # Obtain the user ID of the new maintainer.
    cur = conn.execute("SELECT ID FROM Users WHERE Username = ?", [user])
    user_id = int(cur.fetchone()[0])

    # Execute the notification script.
    subprocess.Popen((notify_cmd, "update", str(user_id), str(pkgbase_id)))


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
