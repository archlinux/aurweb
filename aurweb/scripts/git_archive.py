import argparse
import importlib
import os
import sys
import traceback
from datetime import UTC, datetime

import orjson
import pygit2

from aurweb import config

# Constants
REF = "refs/heads/master"
ORJSON_OPTS = orjson.OPT_SORT_KEYS | orjson.OPT_INDENT_2


def init_repository(git_info) -> None:
    pygit2.init_repository(git_info.path)
    repo = pygit2.Repository(git_info.path)
    for k, v in git_info.config.items():
        repo.config[k] = v


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--spec",
        type=str,
        required=True,
        help="name of spec module in the aurweb.archives.spec package",
    )
    return parser.parse_args()


def update_repository(repo: pygit2.Repository):
    # Use git status to determine file changes
    has_changes = False
    changes = repo.status()
    for filepath, flags in changes.items():
        if flags != pygit2.GIT_STATUS_CURRENT:
            has_changes = True
            break

    if has_changes:
        print("diff detected, committing")
        # Add everything in the tree.
        print("adding files to git tree")

        # Add the tree to staging
        repo.index.read()
        repo.index.add_all()
        repo.index.write()
        tree = repo.index.write_tree()

        # Determine base commit; if repo.head.target raises GitError,
        # we have no current commits
        try:
            base = [repo.head.target]
        except pygit2.GitError:
            base = []

        utcnow = datetime.now(UTC)
        author = pygit2.Signature(
            config.get("git-archive", "author"),
            config.get("git-archive", "author-email"),
            int(utcnow.timestamp()),
            0,
        )

        # Commit the changes
        timestamp = utcnow.strftime("%Y-%m-%d %H:%M:%S")
        title = f"update - {timestamp}"
        repo.create_commit(REF, author, author, title, tree, base)

        print("committed changes")
    else:
        print("no diff detected")


def main() -> int:
    args = parse_args()

    print(f"loading '{args.spec}' spec")
    spec_package = "aurweb.archives.spec"
    module_path = f"{spec_package}.{args.spec}"
    spec_module = importlib.import_module(module_path)
    print(f"loaded '{args.spec}'")

    # Track repositories that the spec modifies. After we run
    # through specs, we want to make a single commit for all
    # repositories that contain changes.
    repos = {}

    print(f"running '{args.spec}' spec...")
    spec = spec_module.Spec()
    for output in spec.generate():
        if not os.path.exists(output.git_info.path / ".git"):
            init_repository(output.git_info)

        path = output.git_info.path / output.filename
        with open(path, "wb") as f:
            f.write(output.data)

        if output.git_info.path not in repos:
            repos[output.git_info.path] = pygit2.Repository(output.git_info.path)

    print(f"done running '{args.spec}' spec")

    print("processing repositories")
    for path in spec.repos:
        print(f"processing repository: {path}")
        update_repository(pygit2.Repository(path))

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception:
        traceback.print_exc()
        sys.exit(1)
