import aurweb.config
from aurweb.testing.requests import Request
from aurweb.time import get_request_timezone, tz_offset


def test_tz_offset_utc():
    offset = tz_offset("UTC")
    assert offset == "+00:00"


def test_tz_offset_mst():
    offset = tz_offset("MST")
    assert offset == "-07:00"


def test_request_timezone():
    request = Request()
    tz = get_request_timezone(request)
    assert tz == aurweb.config.get("options", "default_timezone")


def test_authenticated_request_timezone():
    # Modify a fake request to be authenticated with the
    # America/Los_Angeles timezone.
    request = Request()
    request.user.authenticated = True
    request.user.Timezone = "America/Los_Angeles"

    # Get the request's timezone, it should be America/Los_Angeles.
    tz = get_request_timezone(request)
    assert tz == request.user.Timezone
    assert tz == "America/Los_Angeles"
