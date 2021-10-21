from unittest import mock

import pytest

from redis.client import Pipeline

from aurweb import config, db, logging
from aurweb.models import ApiRateLimit
from aurweb.ratelimit import check_ratelimit
from aurweb.redis import redis_connection
from aurweb.testing import setup_test_db
from aurweb.testing.requests import Request

logger = logging.get_logger(__name__)


@pytest.fixture(autouse=True)
def setup():
    setup_test_db(ApiRateLimit.__tablename__)


@pytest.fixture
def pipeline():
    redis = redis_connection()
    pipeline = redis.pipeline()

    pipeline.delete("ratelimit-ws:127.0.0.1")
    pipeline.delete("ratelimit:127.0.0.1")
    pipeline.execute()

    yield pipeline


def mock_config_getint(section: str, key: str):
    if key == "request_limit":
        return 4
    elif key == "window_length":
        return 100
    return config.getint(section, key)


def mock_config_getboolean(return_value: int = 0):
    def fn(section: str, key: str):
        if section == "ratelimit" and key == "cache":
            return return_value
        return config.getboolean(section, key)
    return fn


def mock_config_get(return_value: str = "none"):
    def fn(section: str, key: str):
        if section == "options" and key == "cache":
            return return_value
        return config.get(section, key)
    return fn


@mock.patch("aurweb.config.getint", side_effect=mock_config_getint)
@mock.patch("aurweb.config.getboolean", side_effect=mock_config_getboolean(1))
@mock.patch("aurweb.config.get", side_effect=mock_config_get("none"))
def test_ratelimit_redis(get: mock.MagicMock, getboolean: mock.MagicMock,
                         getint: mock.MagicMock, pipeline: Pipeline):
    """ This test will only cover aurweb.ratelimit's Redis
    path if a real Redis server is configured. Otherwise,
    it'll use the database. """

    # We'll need a Request for everything here.
    request = Request()

    # Run check_ratelimit for our request_limit. These should succeed.
    for i in range(4):
        assert not check_ratelimit(request)

    # This check_ratelimit should fail, being the 4001th request.
    assert check_ratelimit(request)

    # Delete the Redis keys.
    host = request.client.host
    pipeline.delete(f"ratelimit-ws:{host}")
    pipeline.delete(f"ratelimit:{host}")
    one, two = pipeline.execute()
    assert one and two

    # Should be good to go again!
    assert not check_ratelimit(request)


@mock.patch("aurweb.config.getint", side_effect=mock_config_getint)
@mock.patch("aurweb.config.getboolean", side_effect=mock_config_getboolean(0))
@mock.patch("aurweb.config.get", side_effect=mock_config_get("none"))
def test_ratelimit_db(get: mock.MagicMock, getboolean: mock.MagicMock,
                      getint: mock.MagicMock, pipeline: Pipeline):

    # We'll need a Request for everything here.
    request = Request()

    # Run check_ratelimit for our request_limit. These should succeed.
    for i in range(4):
        assert not check_ratelimit(request)

    # This check_ratelimit should fail, being the 4001th request.
    assert check_ratelimit(request)

    # Delete the ApiRateLimit record.
    with db.begin():
        db.delete(ApiRateLimit)

    # Should be good to go again!
    assert not check_ratelimit(request)
