import warnings
from datetime import UTC, datetime, timedelta
from typing import Generator

import pytest
from sqlalchemy import exc as sa_exc

from aurweb import db
from aurweb.db import create
from aurweb.models.ban import Ban, is_banned
from aurweb.testing.requests import Request


@pytest.fixture(autouse=True)
def setup(db_test):
    return


@pytest.fixture
def ban() -> Generator[Ban]:
    ts = datetime.now(UTC) + timedelta(seconds=30)
    with db.begin():
        ban = create(Ban, IPAddress="127.0.0.1", BanTS=ts)
    yield ban


def test_ban(ban: Ban):
    assert ban.IPAddress == "127.0.0.1"
    assert bool(ban.BanTS)


def test_invalid_ban() -> None:
    with pytest.raises(sa_exc.IntegrityError):
        bad_ban = Ban(BanTS=datetime.now(UTC))

        # We're adding a ban with no primary key; this causes an
        # SQLAlchemy warnings when committing to the DB.
        # Ignore them.
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", sa_exc.SAWarning)
            with db.begin():
                db.add(bad_ban)

    # Since we got a transaction failure, we need to rollback.
    db.rollback()


def test_banned(ban: Ban):
    request = Request()
    request.client.host = "127.0.0.1"
    assert is_banned(request)


def test_not_banned(ban: Ban):
    request = Request()
    request.client.host = "192.168.0.1"
    assert not is_banned(request)
