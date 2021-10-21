import fakeredis

from redis import ConnectionPool, Redis

import aurweb.config

from aurweb import logging

logger = logging.get_logger(__name__)
pool = None


class FakeConnectionPool:
    """ A fake ConnectionPool class which holds an internal reference
    to a fakeredis handle.

    We normally deal with Redis by keeping its ConnectionPool globally
    referenced so we can persist connection state through different calls
    to redis_connection(), and since FakeRedis does not offer a ConnectionPool,
    we craft one up here to hang onto the same handle instance as long as the
    same instance is alive; this allows us to use a similar flow from the
    redis_connection() user's perspective.
    """

    def __init__(self):
        self.handle = fakeredis.FakeStrictRedis()

    def disconnect(self):
        pass


def redis_connection():  # pragma: no cover
    global pool

    disabled = aurweb.config.get("options", "cache") != "redis"

    # If we haven't initialized redis yet, construct a pool.
    if disabled:
        if pool is None:
            logger.debug("Initializing fake Redis instance.")
            pool = FakeConnectionPool()
        return pool.handle
    else:
        if pool is None:
            logger.debug("Initializing real Redis instance.")
            redis_addr = aurweb.config.get("options", "redis_address")
            pool = ConnectionPool.from_url(redis_addr)

    # Create a connection to the pool.
    return Redis(connection_pool=pool)


def kill_redis():
    global pool
    if pool:
        pool.disconnect()
        pool = None
