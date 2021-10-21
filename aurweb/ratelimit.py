from datetime import datetime

from fastapi import Request
from redis.client import Pipeline

from aurweb import config, db, logging
from aurweb.models import ApiRateLimit
from aurweb.redis import redis_connection

logger = logging.get_logger(__name__)


def _update_ratelimit_redis(request: Request, pipeline: Pipeline):
    window_length = config.getint("ratelimit", "window_length")
    now = int(datetime.utcnow().timestamp())
    time_to_delete = now - window_length

    host = request.client.host
    window_key = f"ratelimit-ws:{host}"
    requests_key = f"ratelimit:{host}"

    pipeline.get(window_key)
    window = pipeline.execute()[0]

    if not window or int(window.decode()) < time_to_delete:
        pipeline.set(window_key, now)
        pipeline.expire(window_key, window_length)

        pipeline.set(requests_key, 1)
        pipeline.expire(requests_key, window_length)

        pipeline.execute()
    else:
        pipeline.incr(requests_key)
        pipeline.execute()


def _update_ratelimit_db(request: Request):
    window_length = config.getint("ratelimit", "window_length")
    now = int(datetime.utcnow().timestamp())
    time_to_delete = now - window_length

    with db.begin():
        db.delete(ApiRateLimit, ApiRateLimit.WindowStart < time_to_delete)

    host = request.client.host
    record = db.query(ApiRateLimit, ApiRateLimit.IP == host).first()
    with db.begin():
        if not record:
            record = db.create(ApiRateLimit,
                               WindowStart=now,
                               IP=host, Requests=1)
        else:
            record.Requests += 1

    logger.debug(record.Requests)
    return record


def update_ratelimit(request: Request, pipeline: Pipeline):
    """ Update the ratelimit stored in Redis or the database depending
    on AUR_CONFIG's [options] cache setting.

    This Redis-capable function is slightly different than most. If Redis
    is not configured to use a real server, this function instead uses
    the database to persist tracking of a particular host.

    :param request: FastAPI request
    :param pipeline: redis.client.Pipeline
    :returns: ApiRateLimit record when Redis cache is not configured, else None
    """
    if config.getboolean("ratelimit", "cache"):
        return _update_ratelimit_redis(request, pipeline)
    return _update_ratelimit_db(request)


def check_ratelimit(request: Request):
    """ Increment and check to see if request has exceeded their rate limit.

    :param request: FastAPI request
    :returns: True if the request host has exceeded the rate limit else False
    """
    redis = redis_connection()
    pipeline = redis.pipeline()

    record = update_ratelimit(request, pipeline)

    # Get cache value, else None.
    host = request.client.host
    pipeline.get(f"ratelimit:{host}")
    requests = pipeline.execute()[0]

    # Take into account the split paths. When Redis is used, a
    # valid cache value will be returned which must be converted
    # to an int. Otherwise, use the database record returned
    # by update_ratelimit.
    if not config.getboolean("ratelimit", "cache"):
        # If we got nothing from pipeline.get, we did not use
        # the Redis path of logic: use the DB record's count.
        requests = record.Requests
    else:
        # Otherwise, just case Redis results over to an int.
        requests = int(requests.decode())

    limit = config.getint("ratelimit", "request_limit")
    exceeded_ratelimit = requests > limit
    if exceeded_ratelimit:
        logger.debug(f"{host} has exceeded the ratelimit.")

    return exceeded_ratelimit
