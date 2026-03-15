from typing import Iterable

import orjson
from sqlalchemy import select

from aurweb import config, db
from aurweb.models import PackageBase

from .base import GitInfo, SpecBase, SpecOutput

ORJSON_OPTS = orjson.OPT_SORT_KEYS | orjson.OPT_INDENT_2


class Spec(SpecBase):
    def __init__(self) -> None:
        self.pkgbases_repo = GitInfo(config.get("git-archive", "pkgbases-repo"))

    def generate(self) -> Iterable[SpecOutput]:
        pkgbases = (
            db.get_session()
            .execute(select(PackageBase.Name).order_by(PackageBase.Name.asc()))
            .scalars()
            .all()
        )

        self.add_output(
            "pkgbase.json",
            self.pkgbases_repo,
            orjson.dumps(pkgbases, option=ORJSON_OPTS),
        )
        return self.outputs
