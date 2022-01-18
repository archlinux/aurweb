import json

from http import HTTPStatus

import fastapi
import pytest

from fastapi.responses import JSONResponse

from aurweb import filters, util
from aurweb.testing.requests import Request


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


def test_valid_homepage():
    assert util.valid_homepage("http://google.com")
    assert util.valid_homepage("https://google.com")
    assert not util.valid_homepage("http://[google.com/broken-ipv6")
    assert not util.valid_homepage("https://[google.com/broken-ipv6")

    assert not util.valid_homepage("gopher://gopher.hprc.utoronto.ca/")
