from typing import Iterable

import orjson
from sqlalchemy import select

from aurweb import config, db
from aurweb.models import User

from .base import GitInfo, SpecBase, SpecOutput

ORJSON_OPTS = orjson.OPT_SORT_KEYS | orjson.OPT_INDENT_2


class Spec(SpecBase):
    def __init__(self) -> None:
        self.users_repo = GitInfo(config.get("git-archive", "users-repo"))

    def generate(self) -> Iterable[SpecOutput]:
        users = (
            db.get_session()
            .execute(select(User.Username).order_by(User.Username.asc()))
            .scalars()
            .all()
        )

        self.add_output(
            "users.json",
            self.users_repo,
            orjson.dumps(users, option=ORJSON_OPTS),
        )
        return self.outputs
