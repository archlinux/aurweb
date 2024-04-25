from datetime import UTC, datetime
from zoneinfo import ZoneInfo

import pytest

from aurweb import filters, time


def test_timestamp_to_datetime():
    ts = time.utcnow()
    dt = datetime.fromtimestamp(ts, UTC)
    assert filters.timestamp_to_datetime(ts) == dt


def test_as_timezone():
    ts = time.utcnow()
    dt = filters.timestamp_to_datetime(ts)
    assert filters.as_timezone(dt, "UTC") == dt.astimezone(tz=ZoneInfo("UTC"))


def test_number_format():
    assert filters.number_format(0.222, 2) == "0.22"
    assert filters.number_format(0.226, 2) == "0.23"


def test_extend_query():
    """Test extension of a query via extend_query."""
    query = {"a": "b"}
    extended = filters.extend_query(query, ("a", "c"), ("b", "d"))
    assert extended.get("a") == "c"
    assert extended.get("b") == "d"


def test_to_qs():
    """Test conversion from a query dictionary to a query string."""
    query = {"a": "b", "c": [1, 2, 3]}
    qs = filters.to_qs(query)
    assert qs == "a=b&c=1&c=2&c=3"


@pytest.mark.parametrize(
    "value, args, expected",
    [
        ("", (), ""),
        ("a", (), "a"),
        ("a", (1,), "a"),
        ("%s", ("a",), "a"),
        ("%s", ("ab",), "ab"),
        ("%s%d", ("a", 1), "a1"),
    ],
)
def test_safe_format(value: str, args: tuple, expected: str):
    assert filters.safe_format(value, *args) == expected
