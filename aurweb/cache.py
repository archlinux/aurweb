import pickle
from typing import Any, Callable

from sqlalchemy import func, select
from sqlalchemy.sql import Select

from aurweb import config, db
from aurweb.aur_redis import redis_connection
from aurweb.prometheus import SEARCH_REQUESTS

_redis = redis_connection()


def lambda_cache(key: str, value: Callable[[], Any], expire: int | None = None) -> list:
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


def db_count_cache(key: str, query: Select, expire: int | None = None) -> int:
    """Store and retrieve a count query result via redis cache.

    :param key: Redis key
    :param query: SA 2.0 Select statement
    :param expire: Optional expiration in seconds
    :return: count of results
    """
    result = _redis.get(key)
    if result is None:
        count = (
            db.get_session()
            .execute(select(func.count()).select_from(query.subquery()))
            .scalar()
        )
        _redis.set(key, count)
        if expire:
            _redis.expire(key, expire)
        result = count
    return int(result)


def db_query_cache(key: str, query: Select, expire: int | None = None) -> list:
    """Store and retrieve query results via redis cache.

    :param key: Redis key
    :param query: SA 2.0 Select statement
    :param expire: Optional expiration in seconds
    :return: list of result rows
    """
    result = _redis.get(key)
    if result is None:
        SEARCH_REQUESTS.labels(cache="miss").inc()
        rows = db.get_session().execute(query).all()
        if _redis.dbsize() > config.getint("cache", "max_search_entries", 50000):
            return rows
        _redis.set(key, (result := pickle.dumps(rows)))
        if expire:
            _redis.expire(key, expire)
    else:
        SEARCH_REQUESTS.labels(cache="hit").inc()

    return pickle.loads(result)
