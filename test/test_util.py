from datetime import datetime
from zoneinfo import ZoneInfo

from aurweb import filters, util


def test_timestamp_to_datetime():
    ts = datetime.utcnow().timestamp()
    dt = datetime.utcfromtimestamp(int(ts))
    assert util.timestamp_to_datetime(ts) == dt


def test_as_timezone():
    ts = datetime.utcnow().timestamp()
    dt = util.timestamp_to_datetime(ts)
    assert util.as_timezone(dt, "UTC") == dt.astimezone(tz=ZoneInfo("UTC"))


def test_number_format():
    assert util.number_format(0.222, 2) == "0.22"
    assert util.number_format(0.226, 2) == "0.23"


def test_extend_query():
    """ Test extension of a query via extend_query. """
    query = {"a": "b"}
    extended = util.extend_query(query, ("a", "c"), ("b", "d"))
    assert extended.get("a") == "c"
    assert extended.get("b") == "d"


def test_to_qs():
    """ Test conversion from a query dictionary to a query string. """
    query = {"a": "b", "c": [1, 2, 3]}
    qs = util.to_qs(query)
    assert qs == "a=b&c=1&c=2&c=3"


def test_round():
    assert filters.do_round(1.3) == 1
    assert filters.do_round(1.5) == 2
    assert filters.do_round(2.0) == 2
