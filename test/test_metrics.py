import pytest
from prometheus_client import REGISTRY, generate_latest

from aurweb import db
from aurweb.cache import db_query_cache
from aurweb.models.account_type import USER_ID
from aurweb.models.user import User


@pytest.fixture(autouse=True)
def setup(db_test):
    return


@pytest.fixture
def user() -> User:
    with db.begin():
        user = db.create(
            User,
            Username="test",
            Email="test@example.org",
            RealName="Test User",
            Passwd="testPassword",
            AccountTypeID=USER_ID,
        )
    yield user


@pytest.mark.asyncio
async def test_search_cache_metrics(user: User):
    # Fire off 3 identical queries for caching
    for _ in range(3):
        await db_query_cache("key", db.query(User))

    # Get metrics
    metrics = str(generate_latest(REGISTRY))

    # We should have 1 miss and 2 hits
    assert 'search_requests_total{cache="miss"} 1.0' in metrics
    assert 'search_requests_total{cache="hit"} 2.0' in metrics
