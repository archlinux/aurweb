from typing import Generator
from unittest import mock

import pytest

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
def clear_fakeredis_cache():
    cache._redis.flushall()


def test_db_count_cache(user):
    query = db.query(User)

    # We have no cached value yet.
    assert cache._redis.get("key1") is None

    # Add to cache
    assert cache.db_count_cache("key1", query) == query.count()

    # It's cached now.
    assert cache._redis.get("key1") is not None

    # It does not expire
    assert cache._redis.ttl("key1") == -1

    # Cache a query with an expire.
    value = cache.db_count_cache("key2", query, 100)
    assert value == query.count()

    assert cache._redis.ttl("key2") == 100


def test_db_query_cache(user):
    query = db.query(User)

    # We have no cached value yet.
    assert cache._redis.get("key1") is None

    # Add to cache
    cache.db_query_cache("key1", query)

    # It's cached now.
    assert cache._redis.get("key1") is not None

    # Modify our user and make sure we got a cached value
    user.Username = "changed"
    cached = cache.db_query_cache("key1", query)
    assert cached[0].Username != query.all()[0].Username

    # It does not expire
    assert cache._redis.ttl("key1") == -1

    # Cache a query with an expire.
    value = cache.db_query_cache("key2", query, 100)
    assert len(value) == query.count()
    assert value[0].Username == query.all()[0].Username

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
