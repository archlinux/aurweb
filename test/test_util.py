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
    """Test that git_search matches the full commit if necessary."""
    commit_hash = "0123456789abcdef"
    repo = {commit_hash}
    prefixlen = util.git_search(repo, commit_hash)
    assert prefixlen == 16


def test_git_search_double_commit():
    """Test that git_search matches a shorter prefix length."""
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
        return JSONResponse("{}")

    response = await util.error_or_result(good_route, Request())
    assert response.status_code == HTTPStatus.OK


def test_valid_homepage():
    assert util.valid_homepage("http://google.com")
    assert util.valid_homepage("https://google.com")
    assert not util.valid_homepage("http://[google.com/broken-ipv6")
    assert not util.valid_homepage("https://[google.com/broken-ipv6")

    assert not util.valid_homepage("gopher://gopher.hprc.utoronto.ca/")


def test_parse_ssh_key():
    # Test a valid key.
    pk = """ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyN\
TYAAABBBEURnkiY6JoLyqDE8Li1XuAW+LHmkmLDMW/GL5wY7k4/A+Ta7bjA3MOKrF9j4EuUTvCuNX\
ULxvpfSqheTFWZc+g="""
    prefix, key = util.parse_ssh_key(pk)
    e_prefix, e_key = pk.split()
    assert prefix == e_prefix
    assert key == e_key

    # Test an invalid key with just one word in it.
    with pytest.raises(ValueError):
        util.parse_ssh_key("ssh-rsa")

    # Test a valid key with extra words in it (after the PK).
    pk = pk + " blah blah"
    prefix, key = util.parse_ssh_key(pk)
    assert prefix == e_prefix
    assert key == e_key

    # Test an invalid prefix.
    with pytest.raises(ValueError):
        util.parse_ssh_key("invalid-prefix fake-content")


def test_parse_ssh_keys():
    pks = """ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyN\
TYAAABBBEURnkiY6JoLyqDE8Li1XuAW+LHmkmLDMW/GL5wY7k4/A+Ta7bjA3MOKrF9j4EuUTvCuNX\
ULxvpfSqheTFWZc+g=
ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQDmqEapFMh/ajPHnm1dBweYPeLOUjC0Ydp6uw7rB\
S5KCggUVQR8WfIm+sRYTj2+smGsK6zHMBjFnbzvV11vnMqcnY+Sa4LhIAdwkbt/b8HlGaLj1hCWSh\
a5b5/noeK7L+CECGHdvfJhpxBbhq38YEdFnCGbslk/4NriNcUp/DO81CXb1RzJ9GBFH8ivPW1mbe9\
YbxDwGimZZslg0OZu9UzoAT6xEGyiZsqJkTMbRp1ZYIOv9jHCJxRuxxuN3fzxyT3xE69+vhq2/NJX\
8aRsxGPL9G/XKcaYGS6y6LW4quIBCz/XsTZfx1GmkQeZPYHH8FeE+XC/+toXL/kamxdOQKFYEEpWK\
vTNJCD6JtMClxbIXW9q74nNqG+2SD/VQNMUz/505TK1PbY/4uyFfq5HquHJXQVCBll03FRerNHH2N\
schFne6BFHpa48PCoZNH45wLjFXwUyrGU1HrNqh6ZPdRfBTrTOkgs+BKBxGNeV45aYUPu/cFBSPcB\
fRSo6OFcejKc="""
    keys = util.parse_ssh_keys(pks)
    assert len(keys) == 2

    pfx1, key1, pfx2, key2 = pks.split()
    k1, k2 = keys

    assert pfx1 == k1[0]
    assert key1 == k1[1]

    assert pfx2 == k2[0]
    assert key2 == k2[1]
