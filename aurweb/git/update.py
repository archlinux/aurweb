#!/usr/bin/env python3

import os
import re
import subprocess
import sys
import time

import pygit2
import srcinfo.parse
import srcinfo.utils

import aurweb.config
import aurweb.db

notify_cmd = aurweb.config.get("notifications", "notify-cmd")

repo_path = aurweb.config.get("serve", "repo-path")
repo_regex = aurweb.config.get("serve", "repo-regex")

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


def extract_arch_fields(pkginfo, field):
    values = []

    if field in pkginfo:
        for val in pkginfo[field]:
            values.append({"value": val, "arch": None})

    for arch in pkginfo["arch"]:
        if field + "_" + arch in pkginfo:
            for val in pkginfo[field + "_" + arch]:
                values.append({"value": val, "arch": arch})

    return values


def parse_dep(depstring):
    dep, _, desc = depstring.partition(": ")
    depname = re.sub(r"(<|=|>).*", "", dep)
    depcond = dep[len(depname) :]

    return depname, desc, depcond


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


def save_metadata(metadata, conn, user):  # noqa: C901
    # Obtain package base ID and previous maintainer.
    pkgbase = metadata["pkgbase"]
    cur = conn.execute(
        "SELECT ID, MaintainerUID FROM PackageBases WHERE Name = ?", [pkgbase]
    )
    (pkgbase_id, maintainer_uid) = cur.fetchone()
    was_orphan = not maintainer_uid

    # Obtain the user ID of the new maintainer.
    cur = conn.execute("SELECT ID FROM Users WHERE Username = ?", [user])
    user_id = int(cur.fetchone()[0])

    # Update package base details and delete current packages.
    now = int(time.time())
    conn.execute(
        "UPDATE PackageBases SET ModifiedTS = ?, "
        + "PackagerUID = ?, OutOfDateTS = NULL WHERE ID = ?",
        [now, user_id, pkgbase_id],
    )
    conn.execute(
        "UPDATE PackageBases SET MaintainerUID = ? "
        + "WHERE ID = ? AND MaintainerUID IS NULL",
        [user_id, pkgbase_id],
    )
    for table in ("Sources", "Depends", "Relations", "Licenses", "Groups"):
        conn.execute(
            "DELETE FROM Package"
            + table
            + " WHERE EXISTS ("
            + "SELECT * FROM Packages "
            + "WHERE Packages.PackageBaseID = ? AND "
            + "Package"
            + table
            + ".PackageID = Packages.ID)",
            [pkgbase_id],
        )
    conn.execute("DELETE FROM Packages WHERE PackageBaseID = ?", [pkgbase_id])

    for pkgname in srcinfo.utils.get_package_names(metadata):
        pkginfo = srcinfo.utils.get_merged_package(pkgname, metadata)

        if "epoch" in pkginfo and int(pkginfo["epoch"]) > 0:
            ver = "{:d}:{:s}-{:s}".format(
                int(pkginfo["epoch"]), pkginfo["pkgver"], pkginfo["pkgrel"]
            )
        else:
            ver = "{:s}-{:s}".format(pkginfo["pkgver"], pkginfo["pkgrel"])

        for field in ("pkgdesc", "url"):
            if field not in pkginfo:
                pkginfo[field] = None

        # Create a new package.
        cur = conn.execute(
            "INSERT INTO Packages (PackageBaseID, Name, "
            + "Version, Description, URL) "
            + "VALUES (?, ?, ?, ?, ?)",
            [pkgbase_id, pkginfo["pkgname"], ver, pkginfo["pkgdesc"], pkginfo["url"]],
        )
        conn.commit()
        pkgid = cur.lastrowid

        # Add package sources.
        for source_info in extract_arch_fields(pkginfo, "source"):
            conn.execute(
                "INSERT INTO PackageSources (PackageID, Source, "
                + "SourceArch) VALUES (?, ?, ?)",
                [pkgid, source_info["value"], source_info["arch"]],
            )

        # Add package dependencies.
        for deptype in ("depends", "makedepends", "checkdepends", "optdepends"):
            cur = conn.execute(
                "SELECT ID FROM DependencyTypes WHERE Name = ?", [deptype]
            )
            deptypeid = cur.fetchone()[0]
            for dep_info in extract_arch_fields(pkginfo, deptype):
                depname, depdesc, depcond = parse_dep(dep_info["value"])
                deparch = dep_info["arch"]
                conn.execute(
                    "INSERT INTO PackageDepends (PackageID, "
                    + "DepTypeID, DepName, DepDesc, DepCondition, "
                    + "DepArch) VALUES (?, ?, ?, ?, ?, ?)",
                    [pkgid, deptypeid, depname, depdesc, depcond, deparch],
                )

        # Add package relations (conflicts, provides, replaces).
        for reltype in ("conflicts", "provides", "replaces"):
            cur = conn.execute("SELECT ID FROM RelationTypes WHERE Name = ?", [reltype])
            reltypeid = cur.fetchone()[0]
            for rel_info in extract_arch_fields(pkginfo, reltype):
                relname, _, relcond = parse_dep(rel_info["value"])
                relarch = rel_info["arch"]
                conn.execute(
                    "INSERT INTO PackageRelations (PackageID, "
                    + "RelTypeID, RelName, RelCondition, RelArch) "
                    + "VALUES (?, ?, ?, ?, ?)",
                    [pkgid, reltypeid, relname, relcond, relarch],
                )

        # Add package licenses.
        if "license" in pkginfo:
            for license in pkginfo["license"]:
                cur = conn.execute("SELECT ID FROM Licenses WHERE Name = ?", [license])
                row = cur.fetchone()
                if row:
                    licenseid = row[0]
                else:
                    cur = conn.execute(
                        "INSERT INTO Licenses (Name) " + "VALUES (?)", [license]
                    )
                    conn.commit()
                    licenseid = cur.lastrowid
                conn.execute(
                    "INSERT INTO PackageLicenses (PackageID, "
                    + "LicenseID) VALUES (?, ?)",
                    [pkgid, licenseid],
                )

        # Add package groups.
        if "groups" in pkginfo:
            for group in pkginfo["groups"]:
                cur = conn.execute("SELECT ID FROM `Groups` WHERE Name = ?", [group])
                row = cur.fetchone()
                if row:
                    groupid = row[0]
                else:
                    cur = conn.execute(
                        "INSERT INTO `Groups` (Name) VALUES (?)", [group]
                    )
                    conn.commit()
                    groupid = cur.lastrowid
                conn.execute(
                    "INSERT INTO PackageGroups (PackageID, GroupID) VALUES (?, ?)",
                    [pkgid, groupid],
                )

    # Add user to notification list on adoption.
    if was_orphan:
        cur = conn.execute(
            "SELECT COUNT(*) FROM PackageNotifications WHERE "
            + "PackageBaseID = ? AND UserID = ?",
            [pkgbase_id, user_id],
        )
        if cur.fetchone()[0] == 0:
            conn.execute(
                "INSERT INTO PackageNotifications "
                + "(PackageBaseID, UserID) VALUES (?, ?)",
                [pkgbase_id, user_id],
            )

    conn.commit()


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


def validate_metadata(metadata, commit):  # noqa: C901
    try:
        metadata_pkgbase = metadata["pkgbase"]
    except KeyError:
        die_commit(
            "invalid .SRCINFO, does not contain a pkgbase (is the file empty?)",
            str(commit.id),
        )
    if not re.match(repo_regex, metadata_pkgbase):
        die_commit(f"invalid pkgbase: {metadata_pkgbase:s}", str(commit.id))

    if not metadata["packages"]:
        die_commit("missing pkgname entry", str(commit.id))

    for pkgname in set(metadata["packages"].keys()):
        pkginfo = srcinfo.utils.get_merged_package(pkgname, metadata)

        for field in ("pkgver", "pkgrel", "pkgname"):
            if field not in pkginfo:
                die_commit(f"missing mandatory field: {field:s}", str(commit.id))

        if "epoch" in pkginfo and not pkginfo["epoch"].isdigit():
            die_commit("invalid epoch: {:s}".format(pkginfo["epoch"]), str(commit.id))

        if not re.match(r"[a-z0-9][a-z0-9\.+_-]*$", pkginfo["pkgname"]):
            die_commit(
                "invalid package name: {:s}".format(pkginfo["pkgname"]),
                str(commit.id),
            )

        max_len = {"pkgname": 255, "pkgdesc": 255, "url": 8000}
        for field in max_len.keys():
            if field in pkginfo and len(pkginfo[field]) > max_len[field]:
                die_commit(
                    f"{field:s} field too long: {pkginfo[field]:s}",
                    str(commit.id),
                )

        for field in ("install", "changelog"):
            if field in pkginfo and pkginfo[field] not in commit.tree:
                die_commit(
                    f"missing {field:s} file: {pkginfo[field]:s}",
                    str(commit.id),
                )

        for field in extract_arch_fields(pkginfo, "source"):
            fname = field["value"]
            if len(fname) > 8000:
                die_commit(f"source entry too long: {fname:s}", str(commit.id))
            if "://" in fname or "lp:" in fname:
                continue
            if fname not in commit.tree:
                die_commit(f"missing source file: {fname:s}", str(commit.id))


def validate_blob_size(blob: pygit2.Object, commit: pygit2.Commit):
    if isinstance(blob, pygit2.Blob) and blob.size > max_blob_size:
        die_commit(
            f"maximum blob size ({size_humanize(max_blob_size):s}) exceeded",
            str(commit.id),
        )


def main():  # noqa: C901
    repo = pygit2.Repository(repo_path)

    user = os.environ.get("AUR_USER")
    pkgbase = os.environ.get("AUR_PKGBASE")
    privileged = os.environ.get("AUR_PRIVILEGED", "0") == "1"
    allow_overwrite = (os.environ.get("AUR_OVERWRITE", "0") == "1") and privileged
    warn_or_die = warn if privileged else die

    if len(sys.argv) == 2 and sys.argv[1] == "restore":
        if "refs/heads/" + pkgbase not in repo.listall_references():
            die(f"{sys.argv[1]:s}: repository not found: {pkgbase:s}")
        refname = "refs/heads/master"
        branchref = "refs/heads/" + pkgbase
        sha1_old = sha1_new = repo.lookup_reference(branchref).target
    elif len(sys.argv) == 4:
        refname, sha1_old, sha1_new = sys.argv[1:4]
    else:
        die("invalid arguments")

    if refname != "refs/heads/master":
        die("pushing to a branch other than master is restricted")

    conn = aurweb.db.Connection()

    # Detect and deny non-fast-forwards.
    if sha1_old != "0" * 40 and not allow_overwrite:
        walker = repo.walk(sha1_old, pygit2.GIT_SORT_TOPOLOGICAL)
        walker.hide(sha1_new)
        if next(walker, None) is not None:
            die("denying non-fast-forward (you should pull first)")

    # Prepare the walker that validates new commits.
    walker = repo.walk(sha1_new, pygit2.GIT_SORT_REVERSE)
    if sha1_old != "0" * 40:
        walker.hide(sha1_old)

    head_commit = repo[sha1_new]
    if ".SRCINFO" not in head_commit.tree:
        die_commit("missing .SRCINFO", str(head_commit.id))

    # Read .SRCINFO from the HEAD commit.
    metadata_raw = repo[head_commit.tree[".SRCINFO"].id].data.decode()
    (metadata, errors) = srcinfo.parse.parse_srcinfo(metadata_raw)
    if errors:
        sys.stderr.write(
            "error: The following errors occurred when parsing .SRCINFO in commit\n"
        )
        sys.stderr.write(f"error: {str(head_commit.id):s}:\n")
        for error in errors:
            for err in error["error"]:
                sys.stderr.write("error: line {:d}: {:s}\n".format(error["line"], err))
        exit(1)

    # check if there is a correct .SRCINFO file in the latest revision
    validate_metadata(metadata, head_commit)

    # Compile list of acceptable SPDX license identifiers
    with (
        open(
            "/usr/share/licenses/known_spdx_license_identifiers.txt", encoding="ASCII"
        ) as spdx_identifiers_io,
        open(
            "/usr/share/licenses/known_spdx_license_exceptions.txt", encoding="ASCII"
        ) as spdx_exceptions_io,
    ):
        acceptable_basenames = spdx_identifiers_io.read().splitlines()
        acceptable_basenames += spdx_exceptions_io.read().splitlines()

    # Validate all new commits.
    for commit in walker:
        if "PKGBUILD" not in commit.tree:
            die_commit("missing PKGBUILD", str(commit.id))

        # Iterate over files in root dir
        for treeobj in commit.tree:
            # Don't allow any subdirs besides "keys/" and "LICENSES/"
            if isinstance(treeobj, pygit2.Tree) and treeobj.name not in [
                "keys",
                "LICENSES",
            ]:
                die_commit(
                    "the repository must not contain subdirectories",
                    str(commit.id),
                )

            # Check size of files in root dir
            validate_blob_size(treeobj, commit)

        # If we got a subdir keys/,
        # make sure it only contains a pgp/ subdir with key files
        if "keys" in commit.tree:
            # Check for forbidden files/dirs in keys/
            for keyobj in commit.tree["keys"]:
                if not isinstance(keyobj, pygit2.Tree) or keyobj.name != "pgp":
                    die_commit(
                        "the keys/ subdir may only contain a pgp/ directory",
                        str(commit.id),
                    )
            # Check for forbidden files in keys/pgp/
            if "keys/pgp" in commit.tree:
                for pgpobj in commit.tree["keys/pgp"]:
                    if not isinstance(pgpobj, pygit2.Blob) or not pgpobj.name.endswith(
                        ".asc"
                    ):
                        die_commit(
                            "the subdir may only contain .asc (PGP pub key) files",
                            str(commit.id),
                        )
                    # Check file size for pgp key files
                    validate_blob_size(pgpobj, commit)

        # If we got a subdir LICENSES/,
        # make sure it only contains file names that comply to REUSE.
        # See also: https://reuse.software/spec-3.3/#license-files
        if "LICENSES" in commit.tree:
            # Check for forbidden files in LICENSES/
            for license_obj in commit.tree["LICENSES"]:
                if not isinstance(license_obj, pygit2.Blob) or not any(
                    (
                        license_obj.name.endswith(f".{ext}")
                        for ext in allowed_license_file_exts
                    )
                ):
                    die_commit(
                        "the subdir may only contain files ending in "
                        + " or ".join(f".{ext}" for ext in allowed_license_file_exts),
                        str(commit.id),
                    )

                if (
                    basename := os.path.splitext(os.path.basename(license_obj.name))[0]
                ) not in acceptable_basenames and not basename.startswith(
                    "LicenseRef-"
                ):
                    die_commit(
                        "files in this subdir must either be named after an "
                        "acceptable SPDX license or start with `LicenseRef-`",
                        str(commit.id),
                    )

    # Display a warning if .SRCINFO is unchanged.
    if sha1_old not in ("0000000000000000000000000000000000000000", sha1_new):
        srcinfo_id_old = repo[sha1_old].tree[".SRCINFO"].id
        srcinfo_id_new = repo[sha1_new].tree[".SRCINFO"].id
        if srcinfo_id_old == srcinfo_id_new:
            warn(".SRCINFO unchanged. The package database will not be updated!")

    # Ensure that the package base name matches the repository name.
    metadata_pkgbase = metadata["pkgbase"]
    if metadata_pkgbase != pkgbase:
        die(f"invalid pkgbase: {metadata_pkgbase:s}, expected {pkgbase:s}")

    # Ensure that packages are neither blacklisted nor overwritten.
    pkgbase = metadata["pkgbase"]
    cur = conn.execute("SELECT ID FROM PackageBases WHERE Name = ?", [pkgbase])
    row = cur.fetchone()
    pkgbase_id = row[0] if row else 0

    cur = conn.execute("SELECT Name FROM PackageBlacklist")
    blacklist = [row[0] for row in cur.fetchall()]
    if pkgbase in blacklist:
        warn_or_die(f"pkgbase is blacklisted: {pkgbase:s}")

    cur = conn.execute("SELECT Name, Repo FROM OfficialProviders")
    providers = dict(cur.fetchall())

    for pkgname in srcinfo.utils.get_package_names(metadata):
        pkginfo = srcinfo.utils.get_merged_package(pkgname, metadata)
        pkgname = pkginfo["pkgname"]

        if pkgname in blacklist:
            warn_or_die(f"package is blacklisted: {pkgname:s}")
        if pkgname in providers:
            warn_or_die(
                f"package already provided by [{providers[pkgname]:s}]: {pkgname:s}"
            )

        cur = conn.execute(
            "SELECT COUNT(*) FROM Packages WHERE Name = ? " + "AND PackageBaseID <> ?",
            [pkgname, pkgbase_id],
        )
        if cur.fetchone()[0] > 0:
            die(f"cannot overwrite package: {pkgname:s}")

    # Create a new package base if it does not exist yet.
    if pkgbase_id == 0:
        pkgbase_id = create_pkgbase(conn, pkgbase, user)

    # Store package base details in the database.
    save_metadata(metadata, conn, user)

    # Create (or update) a branch with the name of the package base for better
    # accessibility.
    branchref = "refs/heads/" + pkgbase
    repo.create_reference(branchref, sha1_new, True)

    # Work around a Git bug: The HEAD ref is not updated when using
    # gitnamespaces. This can be removed once the bug fix is included in Git
    # mainline. See
    # http://git.661346.n2.nabble.com/PATCH-receive-pack-Create-a-HEAD-ref-for-ref-namespace-td7632149.html
    # for details.
    headref = "refs/namespaces/" + pkgbase + "/HEAD"
    repo.create_reference(headref, sha1_new, True)

    # Send package update notifications.
    update_notify(conn, user, pkgbase_id)

    # Close the database.
    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
