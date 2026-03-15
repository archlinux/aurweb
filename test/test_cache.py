from typing import Generator
from unittest import mock

import pytest
from sqlalchemy import select

from aurweb import cache, config, db
from aurweb.models.account_type import USER_ID
from aurweb.models.user import User


@pytest.fixture(autouse=True)
def setup(db_test):
    return


@pytest.fixture
def user() -> Generator[User]:
    with db.begin():
        user = db.create(
            User,
            Username="test",
            Email="test@example.org",
            RealName="Test User",
            Passwd="testPassword",
            AccountTypeID=USER_ID,
        )
    yield user


@pytest.fixture(autouse=True)
def clear_fakeredis_cache() -> None:
    cache._redis.flushall()


def test_db_count_cache(user):
    query = select(User.ID, User.Username)
    session = db.get_session()

    # We have no cached value yet.
    assert cache._redis.get("key1") is None

    # Add to cache
    expected_count = len(session.execute(query).all())
    assert cache.db_count_cache("key1", query) == expected_count

    # It's cached now.
    assert cache._redis.get("key1") is not None

    # It does not expire
    assert cache._redis.ttl("key1") == -1

    # Cache a query with an expire.
    value = cache.db_count_cache("key2", query, 100)
    assert value == expected_count

    assert cache._redis.ttl("key2") == 100


def test_db_query_cache(user):
    query = select(User.ID, User.Username)
    session = db.get_session()

    # We have no cached value yet.
    assert cache._redis.get("key1") is None

    # Add to cache
    cache.db_query_cache("key1", query)

    # It's cached now.
    assert cache._redis.get("key1") is not None

    # Modify our user in the DB and make sure we got a stale cached value
    with db.begin():
        user.Username = "changed"
    cached = cache.db_query_cache("key1", query)
    live = session.execute(query).first()
    assert cached[0].Username != live.Username

    # It does not expire
    assert cache._redis.ttl("key1") == -1

    # Cache a query with an expire.
    rows = session.execute(query).all()
    value = cache.db_query_cache("key2", query, 100)
    assert len(value) == len(rows)
    assert value[0].Username == rows[0].Username

    assert cache._redis.ttl("key2") == 100

    # Test "max_search_entries" options
    def mock_max_search_entries(section: str, key: str, fallback: int) -> str:
        if section == "cache" and key == "max_search_entries":
            return 1
        return config.getint(section, key)

    with mock.patch("aurweb.config.getint", side_effect=mock_max_search_entries):
        # Try to add another entry (we already have 2)
        cache.db_query_cache("key3", query)

        # Make sure it was not added because it exceeds our max.
        assert cache._redis.get("key3") is None
