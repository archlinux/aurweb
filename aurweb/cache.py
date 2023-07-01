import pickle

from sqlalchemy import orm

from aurweb import config
from aurweb.aur_redis import redis_connection

_redis = redis_connection()


async def db_count_cache(key: str, query: orm.Query, expire: int = None) -> int:
    """Store and retrieve a query.count() via redis cache.

    :param key: Redis key
    :param query: SQLAlchemy ORM query
    :param expire: Optional expiration in seconds
    :return: query.count()
    """
    result = _redis.get(key)
    if result is None:
        _redis.set(key, (result := int(query.count())))
        if expire:
            _redis.expire(key, expire)
    return int(result)


async def db_query_cache(key: str, query: orm.Query, expire: int = None):
    """Store and retrieve query results via redis cache.

    :param key: Redis key
    :param query: SQLAlchemy ORM query
    :param expire: Optional expiration in seconds
    :return: query.all()
    """
    result = _redis.get(key)
    if result is None:
        if _redis.dbsize() > config.getint("cache", "max_search_entries", 50000):
            return query.all()
        _redis.set(key, (result := pickle.dumps(query.all())), ex=expire)
        if expire:
            _redis.expire(key, expire)

    return pickle.loads(result)
