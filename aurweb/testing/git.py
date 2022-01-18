import os
import shlex

from subprocess import PIPE, Popen
from typing import Tuple

import py

from aurweb.models import Package
from aurweb.templates import base_template
from aurweb.testing.filelock import FileLock


class GitRepository:
    """
    A Git repository class to be used for testing.

    Expects a `tmpdir` fixture on construction, which an 'aur.git'
    git repository will be created in. After this class is constructed,
    users can call GitRepository.exec for git repository operations.
    """

    def __init__(self, tmpdir: py.path.local):
        self.file_lock = FileLock(tmpdir, "aur.git")
        self.file_lock.lock(on_create=self._setup)

    def _exec(self, cmdline: str, cwd: str) -> Tuple[int, str, str]:
        args = shlex.split(cmdline)
        proc = Popen(args, cwd=cwd, stdout=PIPE, stderr=PIPE)
        out, err = proc.communicate()
        return (proc.returncode, out.decode().strip(), err.decode().strip())

    def _exec_repository(self, cmdline: str) -> Tuple[int, str, str]:
        return self._exec(cmdline, cwd=str(self.file_lock.path))

    def exec(self, cmdline: str) -> Tuple[int, str, str]:
        return self._exec_repository(cmdline)

    def _setup(self, path: str) -> None:
        """
        Setup the git repository from scratch.

        Create the `path` directory and run the INSTALL recommended
        git initialization commands inside of it. Additionally, install
        aurweb.git.update to {path}/hooks/update.

        :param path: Repository path not yet created
        """

        os.makedirs(path)

        commands = [
            "git init -q",
            "git config --local transfer.hideRefs '^refs/'",
            "git config --local --add transfer.hideRefs '!refs/'",
            "git config --local --add transfer.hideRefs '!HEAD'",
            "git config --local commit.gpgsign false",
            "git config --local user.name 'Test User'",
            "git config --local user.email 'test@example.org'",
        ]
        for cmdline in commands:
            return_code, out, err = self.exec(cmdline)
            assert return_code == 0

        # This is also done in the INSTALL script to give the `aur`
        # ssh user permissions on the repository. We don't need it
        # during testing, since our testing user will be controlling
        # the repository. It is left here as a note.
        # self.exec("chown -R aur .")

    def commit(self, pkg: Package, message: str):
        """
        Commit a Package record to the git repository.

        This function generates a PKGBUILD and .SRCINFO based on
        `pkg`, then commits them to the repository with the
        `message` commit message.

        :param pkg: Package instance
        :param message: Commit message
        :return: Output of `git rev-parse HEAD` after committing
        """
        ref = f"refs/namespaces/{pkg.Name}/refs/heads/master"
        rc, out, err = self.exec(f"git checkout -q --orphan {ref}")
        assert rc == 0, f"{(rc, out, err)}"

        # Path to aur.git repository.
        repo = os.path.join(self.file_lock.path)

        licenses = [f"'{p.License.Name}'" for p in pkg.package_licenses]
        depends = [f"'{p.DepName}'" for p in pkg.package_dependencies]
        pkgbuild = base_template("testing/PKGBUILD.j2")
        pkgbuild_path = os.path.join(repo, "PKGBUILD")
        with open(pkgbuild_path, "w") as f:
            data = pkgbuild.render(pkg=pkg, licenses=licenses, depends=depends)
            f.write(data)

        srcinfo = base_template("testing/SRCINFO.j2")
        srcinfo_path = os.path.join(repo, ".SRCINFO")
        with open(srcinfo_path, "w") as f:
            f.write(srcinfo.render(pkg=pkg))

        rc, out, err = self.exec("git add PKGBUILD .SRCINFO")
        assert rc == 0, f"{(rc, out, err)}"

        rc, out, err = self.exec(f"git commit -q -m '{message}'")
        assert rc == 0, f"{(rc, out, err)}"

        # Return stdout of `git rev-parse HEAD`, which is the new commit hash.
        return self.exec("git rev-parse HEAD")[1]
