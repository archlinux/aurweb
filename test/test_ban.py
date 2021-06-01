import warnings

from datetime import datetime, timedelta

import pytest

from sqlalchemy import exc as sa_exc

from aurweb.db import create
from aurweb.models.ban import Ban, is_banned
from aurweb.testing import setup_test_db
from aurweb.testing.requests import Request

ban = request = None


@pytest.fixture(autouse=True)
def setup():
    global ban, request

    setup_test_db("Bans")

    ts = datetime.utcnow() + timedelta(seconds=30)
    ban = create(Ban, IPAddress="127.0.0.1", BanTS=ts)
    request = Request()


def test_ban():
    assert ban.IPAddress == "127.0.0.1"
    assert bool(ban.BanTS)


def test_invalid_ban():
    from aurweb.db import session

    with pytest.raises(sa_exc.IntegrityError,
                       match="NOT NULL constraint failed: Bans.IPAddress"):
        bad_ban = Ban(BanTS=datetime.utcnow())
        session.add(bad_ban)

        # We're adding a ban with no primary key; this causes an
        # SQLAlchemy warnings when committing to the DB.
        # Ignore them.
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", sa_exc.SAWarning)
            session.commit()

    # Since we got a transaction failure, we need to rollback.
    session.rollback()


def test_banned():
    request.client.host = "127.0.0.1"
    assert is_banned(request)


def test_not_banned():
    request.client.host = "192.168.0.1"
    assert not is_banned(request)
