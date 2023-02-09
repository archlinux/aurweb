from typing import Iterable

import orjson

from aurweb import config, db
from aurweb.models import Package, PackageBase

from .base import GitInfo, SpecBase, SpecOutput

ORJSON_OPTS = orjson.OPT_SORT_KEYS | orjson.OPT_INDENT_2


class Spec(SpecBase):
    def __init__(self) -> "Spec":
        self.pkgnames_repo = GitInfo(config.get("git-archive", "pkgnames-repo"))

    def generate(self) -> Iterable[SpecOutput]:
        query = (
            db.query(Package.Name)
            .join(PackageBase, PackageBase.ID == Package.PackageBaseID)
            .order_by(Package.Name.asc())
            .all()
        )
        pkgnames = [pkg.Name for pkg in query]

        self.add_output(
            "pkgname.json",
            self.pkgnames_repo,
            orjson.dumps(pkgnames, option=ORJSON_OPTS),
        )
        return self.outputs
