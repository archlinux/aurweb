from datetime import datetime
from zoneinfo import ZoneInfo

from aurweb import util


def test_timestamp_to_datetime():
    ts = datetime.utcnow().timestamp()
    dt = datetime.utcfromtimestamp(int(ts))
    assert util.timestamp_to_datetime(ts) == dt


def test_as_timezone():
    ts = datetime.utcnow().timestamp()
    dt = util.timestamp_to_datetime(ts)
    assert util.as_timezone(dt, "UTC") == dt.astimezone(tz=ZoneInfo("UTC"))
