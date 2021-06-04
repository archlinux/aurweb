import pytest

from sqlalchemy.exc import IntegrityError

from aurweb.db import create
from aurweb.models.api_rate_limit import ApiRateLimit
from aurweb.testing import setup_test_db


@pytest.fixture(autouse=True)
def setup():
    setup_test_db("ApiRateLimit")


def test_api_rate_key_creation():
    rate = create(ApiRateLimit, IP="127.0.0.1", Requests=10, WindowStart=1)
    assert rate.IP == "127.0.0.1"
    assert rate.Requests == 10
    assert rate.WindowStart == 1


def test_api_rate_key_ip_default():
    api_rate_limit = create(ApiRateLimit, Requests=10, WindowStart=1)
    assert api_rate_limit.IP == str()


def test_api_rate_key_null_requests_raises_exception():
    from aurweb.db import session
    with pytest.raises(IntegrityError):
        create(ApiRateLimit, IP="127.0.0.1", WindowStart=1)
    session.rollback()


def test_api_rate_key_null_window_start_raises_exception():
    from aurweb.db import session
    with pytest.raises(IntegrityError):
        create(ApiRateLimit, IP="127.0.0.1", WindowStart=1)
    session.rollback()
