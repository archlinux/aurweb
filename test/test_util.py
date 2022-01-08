import json

from datetime import datetime
from http import HTTPStatus
from zoneinfo import ZoneInfo

import fastapi
import pytest

from fastapi.responses import JSONResponse

from aurweb import filters, util
from aurweb.testing.requests import Request


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


def test_git_search():
    """ Test that git_search matches the full commit if necessary. """
    commit_hash = "0123456789abcdef"
    repo = {commit_hash}
    prefixlen = util.git_search(repo, commit_hash)
    assert prefixlen == 16


def test_git_search_double_commit():
    """ Test that git_search matches a shorter prefix length. """
    commit_hash = "0123456789abcdef"
    repo = {commit_hash[:13]}
    # Locate the shortest prefix length that matches commit_hash.
    prefixlen = util.git_search(repo, commit_hash)
    assert prefixlen == 13


@pytest.mark.asyncio
async def test_error_or_result():

    async def route(request: fastapi.Request):
        raise RuntimeError("No response returned.")

    response = await util.error_or_result(route, Request())
    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR

    data = json.loads(response.body)
    assert data.get("error") == "No response returned."

    async def good_route(request: fastapi.Request):
        return JSONResponse()

    response = await util.error_or_result(good_route, Request())
    assert response.status_code == HTTPStatus.OK
