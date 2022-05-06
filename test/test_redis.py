from unittest import mock

import pytest

import aurweb.config
from aurweb.aur_redis import redis_connection


@pytest.fixture
def redis():
    """Create a RedisStub."""

    def mock_get(section, key):
        return "none"

    with mock.patch("aurweb.config.get", side_effect=mock_get):
        aurweb.config.rehash()
        redis = redis_connection()
    aurweb.config.rehash()

    yield redis


def test_redis_stub(redis):
    # We don't yet have a test key set.
    assert redis.get("test") is None

    # Set the test key to abc.
    redis.set("test", "abc")
    assert redis.get("test").decode() == "abc"

    # Test expire.
    redis.expire("test", 0)
    assert redis.get("test") is None

    # Now, set the test key again and use delete() on it.
    redis.set("test", "abc")
    assert redis.get("test").decode() == "abc"
    redis.delete("test")
    assert redis.get("test") is None
