import pytest

from sqlalchemy.exc import IntegrityError

from aurweb import db
from aurweb.models.api_rate_limit import ApiRateLimit


@pytest.fixture(autouse=True)
def setup(db_test):
    return


def test_api_rate_key_creation():
    with db.begin():
        rate = db.create(ApiRateLimit, IP="127.0.0.1", Requests=10,
                         WindowStart=1)
    assert rate.IP == "127.0.0.1"
    assert rate.Requests == 10
    assert rate.WindowStart == 1


def test_api_rate_key_ip_default():
    with db.begin():
        api_rate_limit = db.create(ApiRateLimit, Requests=10, WindowStart=1)
    assert api_rate_limit.IP == str()


def test_api_rate_key_null_requests_raises_exception():
    with pytest.raises(IntegrityError):
        ApiRateLimit(IP="127.0.0.1", WindowStart=1)


def test_api_rate_key_null_window_start_raises_exception():
    with pytest.raises(IntegrityError):
        ApiRateLimit(IP="127.0.0.1", Requests=1)
