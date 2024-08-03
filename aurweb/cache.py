import pickle

from sqlalchemy import orm
from typing import Callable, Any

from aurweb import config
from aurweb.aur_redis import redis_connection
from aurweb.prometheus import SEARCH_REQUESTS

_redis = redis_connection()


def lambda_cache(key: str, value: Callable[[], Any], expire: int = None) -> list:
    """Store and retrieve lambda results via redis cache.

    :param key: Redis key
    :param value: Lambda callable returning the value
    :param expire: Optional expiration in seconds
    :return: result of callable or cache
    """
    result = _redis.get(key)
    if result is not None:
        return pickle.loads(result)

    _redis.set(key, (pickle.dumps(result := value())), ex=expire)
    return result


def db_count_cache(key: str, query: orm.Query, expire: int = None) -> int:
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


def db_query_cache(key: str, query: orm.Query, expire: int = None) -> list:
    """Store and retrieve query results via redis cache.

    :param key: Redis key
    :param query: SQLAlchemy ORM query
    :param expire: Optional expiration in seconds
    :return: query.all()
    """
    result = _redis.get(key)
    if result is None:
        SEARCH_REQUESTS.labels(cache="miss").inc()
        if _redis.dbsize() > config.getint("cache", "max_search_entries", 50000):
            return query.all()
        _redis.set(key, (result := pickle.dumps(query.all())))
        if expire:
            _redis.expire(key, expire)
    else:
        SEARCH_REQUESTS.labels(cache="hit").inc()

    return pickle.loads(result)
