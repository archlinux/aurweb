#!/usr/bin/env python3

import os
import sys
import time

import pygit2
from alpm.alpm_srcinfo import MergedPackage, SourceInfoError, source_info_from_str
from alpm.alpm_srcinfo.source_info.v1.package_base import PackageBase
from alpm.alpm_types import (
    Architecture,
    OptionalDependency,
    PackageRelation,
    SonameV1,
    SonameV1Type,
)
from alpm.type_aliases import RelationOrSoname, SourceInfo

import aurweb.config
import aurweb.db
from aurweb.git.update_common import (
    allowed_license_file_exts,
    create_pkgbase,
    die,
    die_commit,
    update_notify,
    validate_blob_size,
    warn,
)

repo_path = aurweb.config.get("serve", "repo-path")

alpm_parser = aurweb.config.getboolean("update", "alpm-parser")


# A generic relation that can be either a PackageRelation, SonameV1, SonameV2,
# or OptionalDependency.
type GenericRelation = RelationOrSoname | OptionalDependency


def sql_rel_name(relation: GenericRelation) -> str:
    """Create a str to be used in SQL queries for relation name."""

    if isinstance(relation, (PackageRelation, OptionalDependency, SonameV1)):
        return str(relation.name)

    # SonameV2
    return f"{relation.prefix}:{relation.soname}"


def sql_rel_description(relation: GenericRelation) -> str:
    """Create a str to be used in SQL queries for dependency description.

    Always returns an empty str for non-OptionalDependency types.
    """
    if isinstance(relation, OptionalDependency) and relation.description is not None:
        return str(relation.description)

    return ""


def sql_rel_requirement(relation: GenericRelation) -> str:
    """Create a str to be used in SQL queries for version requirements.

    Returns an empty str if no version requirement is specified.

    For legacy reasons, unversioned and explicit SonameV1 are converted accordingly:
      - "libfoo.so=1-64" -> "=1-64"
      - "libfoo.so=libfoo.so-64" -> "=libfoo.so-64"
    """
    if (
        isinstance(relation, (PackageRelation, OptionalDependency))
        and relation.version_requirement is not None
    ):
        return str(relation.version_requirement)

    if isinstance(relation, SonameV1):
        elf_arch = "" if relation.architecture is None else f"-{relation.architecture}"
        match relation.form:
            case SonameV1Type.UNVERSIONED:
                return f"={relation.soname}{elf_arch}"
            case SonameV1Type.EXPLICIT:
                return f"={relation.version}{elf_arch}"

    return ""


def sql_architecture(arch: Architecture) -> str | None:
    """Create a str | None to be used in SQL queries for architecture.

    Translates 'any' to None.
    """
    return None if arch.is_any else str(arch)


def save_metadata(metadata: SourceInfo, conn, user):  # noqa: C901
    # Obtain package base ID and previous maintainer.
    cur = conn.execute(
        "SELECT ID, MaintainerUID FROM PackageBases WHERE Name = ?",
        [metadata.base.name],
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

    version: str = str(metadata.base.version)

    for package in metadata.packages:
        # Architecture doesn't matter here, as we are only reading
        # non-arch-specific fields from merged_pkg.
        merged_pkg = MergedPackage(Architecture(), metadata.base, package)

        # Create a new package.
        cur = conn.execute(
            "INSERT INTO Packages (PackageBaseID, Name, "
            + "Version, Description, URL) "
            + "VALUES (?, ?, ?, ?, ?)",
            [
                pkgbase_id,
                merged_pkg.name,
                version,
                merged_pkg.description,
                str(merged_pkg.url),
            ],
        )
        conn.commit()
        pkgid = cur.lastrowid

        for arch in metadata.base.architectures:
            # Arch-specific merged_pkg
            merged_pkg = MergedPackage(arch, metadata.base, package)

            # Add package sources.
            for merged_source in merged_pkg.sources:
                conn.execute(
                    "INSERT INTO PackageSources (PackageID, Source, "
                    + "SourceArch) VALUES (?, ?, ?)",
                    [pkgid, str(merged_source.source), sql_architecture(arch)],
                )

            # Add package dependencies.
            dependency_groups: dict[str, list[GenericRelation]] = {
                "depends": merged_pkg.dependencies,
                "makedepends": merged_pkg.make_dependencies,
                "checkdepends": merged_pkg.check_dependencies,
                "optdepends": merged_pkg.optional_dependencies,
            }
            for deptype, dependencies in dependency_groups.items():
                cur = conn.execute(
                    "SELECT ID FROM DependencyTypes WHERE Name = ?", [deptype]
                )
                deptypeid = cur.fetchone()[0]

                for dep in dependencies:
                    conn.execute(
                        "INSERT INTO PackageDepends (PackageID, "
                        + "DepTypeID, DepName, DepDesc, DepCondition, "
                        + "DepArch) VALUES (?, ?, ?, ?, ?, ?)",
                        [
                            pkgid,
                            deptypeid,
                            sql_rel_name(dep),
                            sql_rel_description(dep),
                            sql_rel_requirement(dep),
                            sql_architecture(arch),
                        ],
                    )

            # Add package relations (conflicts, provides, replaces).
            relation_groups: dict[str, list[RelationOrSoname]] = {
                "conflicts": merged_pkg.conflicts,
                "provides": merged_pkg.provides,
                "replaces": merged_pkg.replaces,
            }
            for reltype, relations in relation_groups.items():
                cur = conn.execute(
                    "SELECT ID FROM RelationTypes WHERE Name = ?", [reltype]
                )
                reltypeid = cur.fetchone()[0]
                for rel in relations:
                    conn.execute(
                        "INSERT INTO PackageRelations (PackageID, "
                        + "RelTypeID, RelName, RelCondition, RelArch) "
                        + "VALUES (?, ?, ?, ?, ?)",
                        [
                            pkgid,
                            reltypeid,
                            sql_rel_name(rel),
                            sql_rel_requirement(rel),
                            sql_architecture(arch),
                        ],
                    )

        # Add package licenses.
        for lic in merged_pkg.licenses:
            cur = conn.execute("SELECT ID FROM Licenses WHERE Name = ?", [str(lic)])
            row = cur.fetchone()
            if row:
                licenseid = row[0]
            else:
                cur = conn.execute(
                    "INSERT INTO Licenses (Name) " + "VALUES (?)", [str(lic)]
                )
                conn.commit()
                licenseid = cur.lastrowid
            conn.execute(
                "INSERT INTO PackageLicenses (PackageID, " + "LicenseID) VALUES (?, ?)",
                [pkgid, licenseid],
            )

        # Add package groups.
        for group in merged_pkg.groups:
            cur = conn.execute("SELECT ID FROM `Groups` WHERE Name = ?", [group])
            row = cur.fetchone()
            if row:
                groupid = row[0]
            else:
                cur = conn.execute("INSERT INTO `Groups` (Name) VALUES (?)", [group])
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


def validate_metadata(metadata: SourceInfo, commit):  # noqa: C901
    for pkg_overrides in metadata.packages:
        # Architecture doesn't matter here, as we are only reading
        # non-arch-specific fields from merged_pkg.
        merged_pkg = MergedPackage(Architecture(), metadata.base, pkg_overrides)

        max_len = {
            "name": ("pkgname", 255),
            "description": ("pkgdesc", 255),
            "url": ("url", 8000),
        }
        for attr, (field, limit) in max_len.items():
            value = str(getattr(merged_pkg, attr))
            if len(value) > limit:
                die_commit(
                    f"{field:s} field too long: {value}",
                    str(commit.id),
                )

        for field in ("install", "changelog"):
            value = getattr(merged_pkg, field)
            if value is not None and value not in commit.tree:
                die_commit(
                    f"missing {field:s} file: {value}",
                    str(commit.id),
                )

        for arch in metadata.base.architectures:
            # Arch-specific merged_pkg
            merged_pkg = MergedPackage(arch, metadata.base, pkg_overrides)

            for source in merged_pkg.sources:
                fname = str(source.source)
                if len(fname) > 8000:
                    die_commit(f"source entry too long: {fname:s}", str(commit.id))
                if "://" in fname or "lp:" in fname:
                    continue
                if fname not in commit.tree:
                    die_commit(f"missing source file: {fname:s}", str(commit.id))


def main() -> None:  # noqa: C901
    repo = pygit2.Repository(repo_path)

    user: str = os.environ.get("AUR_USER")
    pkgbase: str = os.environ.get("AUR_PKGBASE")
    privileged: bool = os.environ.get("AUR_PRIVILEGED", "0") == "1"
    allow_overwrite: bool = (os.environ.get("AUR_OVERWRITE", "0") == "1") and privileged
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

    try:
        metadata: SourceInfo = source_info_from_str(metadata_raw)
    except SourceInfoError as e:
        err_msg = str(e).replace("alpm_srcinfo.SourceInfoError: ", "")
        die_commit(err_msg, str(head_commit.id))

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
    metadata_pkgbase: PackageBase = metadata.base
    if metadata_pkgbase.name != pkgbase:
        die(f"invalid pkgbase: {metadata_pkgbase.name:s}, expected {pkgbase:s}")

    # Ensure that packages are neither blacklisted nor overwritten.
    pkgbase: PackageBase = metadata.base
    cur = conn.execute("SELECT ID FROM PackageBases WHERE Name = ?", [pkgbase.name])
    row = cur.fetchone()
    pkgbase_id = row[0] if row else 0

    cur = conn.execute("SELECT Name FROM PackageBlacklist")
    blacklist = [row[0] for row in cur.fetchall()]
    if pkgbase.name in blacklist:
        warn_or_die(f"pkgbase is blacklisted: {pkgbase.name:s}")

    cur = conn.execute("SELECT Name, Repo FROM OfficialProviders")
    providers = dict(cur.fetchall())

    for package in metadata.packages:
        if package.name in blacklist:
            warn_or_die(f"package is blacklisted: {package.name:s}")
        if package.name in providers:
            warn_or_die(
                f"package already provided by "
                f"[{providers[package.name]:s}]: {package.name:s}"
            )

        cur = conn.execute(
            "SELECT COUNT(*) FROM Packages WHERE Name = ? " + "AND PackageBaseID <> ?",
            [package.name, pkgbase_id],
        )
        if cur.fetchone()[0] > 0:
            die(f"cannot overwrite package: {package.name:s}")

    # Create a new package base if it does not exist yet.
    if pkgbase_id == 0:
        pkgbase_id = create_pkgbase(conn, pkgbase.name, user)

    # Store package base details in the database.
    save_metadata(metadata, conn, user)

    # Create (or update) a branch with the name of the package base for better
    # accessibility.
    branchref = "refs/heads/" + pkgbase.name
    repo.create_reference(branchref, sha1_new, True)

    # Work around a Git bug: The HEAD ref is not updated when using
    # gitnamespaces. This can be removed once the bug fix is included in Git
    # mainline. See
    # http://git.661346.n2.nabble.com/PATCH-receive-pack-Create-a-HEAD-ref-for-ref-namespace-td7632149.html
    # for details.
    headref = "refs/namespaces/" + pkgbase.name + "/HEAD"
    repo.create_reference(headref, sha1_new, True)

    # Send package update notifications.
    update_notify(conn, user, pkgbase_id)

    # Close the database.
    cur.close()
    conn.close()


if __name__ == "__main__":
    if alpm_parser:
        main()
    else:
        from aurweb.git.update_legacy import main as legacy_main

        legacy_main()
