from redis import Redis
from sqlalchemy import orm


async def db_count_cache(redis: Redis, key: str, query: orm.Query,
                         expire: int = None) -> int:
    """ Store and retrieve a query.count() via redis cache.

    :param redis: Redis handle
    :param key: Redis key
    :param query: SQLAlchemy ORM query
    :param expire: Optional expiration in seconds
    :return: query.count()
    """
    result = redis.get(key)
    if result is None:
        redis.set(key, (result := int(query.count())))
        if expire:
            redis.expire(key, expire)
    return int(result)
