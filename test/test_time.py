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

    # Default timezone
    dtz = aurweb.config.get("options", "default_timezone")
    assert get_request_timezone(request) == dtz

    # Timezone from query params
    request.query_params = {"timezone": "Europe/Berlin"}
    assert get_request_timezone(request) == "Europe/Berlin"

    # Timezone from authenticated user.
    request.query_params = {}
    request.user.authenticated = True
    request.user.Timezone = "America/Los_Angeles"
    assert get_request_timezone(request) == "America/Los_Angeles"

    # Timezone from authenticated user with query param
    # Query param should have precedence
    request.query_params = {"timezone": "Europe/Berlin"}
    assert get_request_timezone(request) == "Europe/Berlin"
