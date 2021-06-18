from datetime import datetime

from aurweb import util


def test_timestamp_to_datetime():
    ts = datetime.utcnow().timestamp()
    dt = datetime.utcfromtimestamp(int(ts))
    assert util.timestamp_to_datetime(ts) == dt
