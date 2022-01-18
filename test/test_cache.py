import pytest

from aurweb import cache, db
from aurweb.models.account_type import USER_ID
from aurweb.models.user import User


@pytest.fixture(autouse=True)
def setup(db_test):
    return


class StubRedis:
    """ A class which acts as a RedisConnection without using Redis. """

    cache = dict()
    expires = dict()

    def get(self, key, *args):
        if "key" not in self.cache:
            self.cache[key] = None
        return self.cache[key]

    def set(self, key, *args):
        self.cache[key] = list(args)[0]

    def expire(self, key, *args):
        self.expires[key] = list(args)[0]

    async def execute(self, command, key, *args):
        f = getattr(self, command)
        return f(key, *args)


@pytest.fixture
def redis():
    yield StubRedis()


@pytest.mark.asyncio
async def test_db_count_cache(redis):
    db.create(User, Username="user1",
              Email="user1@example.org",
              Passwd="testPassword",
              AccountTypeID=USER_ID)

    query = db.query(User)

    # Now, perform several checks that db_count_cache matches query.count().

    # We have no cached value yet.
    assert await cache.db_count_cache(redis, "key1", query) == query.count()

    # It's cached now.
    assert await cache.db_count_cache(redis, "key1", query) == query.count()


@pytest.mark.asyncio
async def test_db_count_cache_expires(redis):
    db.create(User, Username="user1",
              Email="user1@example.org",
              Passwd="testPassword",
              AccountTypeID=USER_ID)

    query = db.query(User)

    # Cache a query with an expire.
    value = await cache.db_count_cache(redis, "key1", query, 100)
    assert value == query.count()

    assert redis.expires["key1"] == 100
