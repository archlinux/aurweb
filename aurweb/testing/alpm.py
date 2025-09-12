import hashlib
import os
import re
import shutil
import subprocess

from aurweb import aur_logging, util
from aurweb.templates import base_template

logger = aur_logging.get_logger(__name__)


class AlpmDatabase:
    """
    Fake libalpm database management class.

    This class can be used to add or remove packages from a
    test repository.
    """

    repo = "test"

    def __init__(self, database_root: str):
        self.root = database_root
        self.local = os.path.join(self.root, "local")
        self.remote = os.path.join(self.root, "remote")
        self.repopath = os.path.join(self.remote, self.repo)

        # Make directories.
        os.makedirs(self.local)
        os.makedirs(self.remote)

    def _get_pkgdir(self, pkgname: str, pkgver: str, repo: str) -> str:
        pkgfile = f"{pkgname}-{pkgver}-1"
        pkgdir = os.path.join(self.remote, repo, pkgfile)
        os.makedirs(pkgdir)
        return pkgdir

    def add(
        self, pkgname: str, pkgver: str, arch: str, provides: list[str] = []
    ) -> None:
        context = {
            "pkgname": pkgname,
            "pkgver": pkgver,
            "arch": arch,
            "provides": provides,
        }
        template = base_template("testing/alpm_package.j2")
        pkgdir = self._get_pkgdir(pkgname, pkgver, self.repo)
        desc = os.path.join(pkgdir, "desc")
        with open(desc, "w") as f:
            f.write(template.render(context))

        self.compile()

    def remove(self, pkgname: str):
        files = os.listdir(self.repopath)
        logger.info("Files: %s", files)
        expr = "^" + pkgname + r"-[0-9.]+-1$"
        logger.info("Expression: %s", expr)
        to_delete = filter(lambda e: re.match(expr, e), files)

        for target in to_delete:
            logger.info("Deleting %s", target)
            path = os.path.join(self.repopath, target)
            shutil.rmtree(path)

        self.compile()

    def clean(self) -> None:
        db_file = os.path.join(self.remote, "test.db")
        try:
            os.remove(db_file)
        except Exception:
            pass

    def compile(self) -> None:
        self.clean()
        cmdline = ["bash", "-c", "bsdtar -czvf ../test.db *"]
        proc = subprocess.run(cmdline, cwd=self.repopath)
        assert proc.returncode == 0, (
            f"Bad return code while creating alpm database: {proc.returncode}"
        )

        # Print out the md5 hash value of the new test.db.
        test_db = os.path.join(self.remote, "test.db")
        db_hash = util.file_hash(test_db, hashlib.md5)
        logger.debug("%s: %s", test_db, db_hash)
