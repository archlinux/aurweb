from unittest import mock

import pytest

import aurweb.config

from aurweb.redis import redis_connection


@pytest.fixture
def rediss():
    """ Create a RedisStub. """
    def mock_get(section, key):
        return "none"

    with mock.patch("aurweb.config.get", side_effect=mock_get):
        aurweb.config.rehash()
        redis = redis_connection()
    aurweb.config.rehash()

    yield redis


def test_redis_stub(rediss):
    # We don't yet have a test key set.
    assert rediss.get("test") is None

    # Set the test key to abc.
    rediss.set("test", "abc")
    assert rediss.get("test").decode() == "abc"

    # Test expire.
    rediss.expire("test", 0)
    assert rediss.get("test") is None

    # Now, set the test key again and use delete() on it.
    rediss.set("test", "abc")
    assert rediss.get("test").decode() == "abc"
    rediss.delete("test")
    assert rediss.get("test") is None
