import json
from http import HTTPStatus

import fastapi
import pytest
from fastapi.responses import JSONResponse

from aurweb import db, filters, util
from aurweb.models.user import User
from aurweb.testing.requests import Request


def test_round() -> None:
    assert filters.do_round(1.3) == 1
    assert filters.do_round(1.5) == 2
    assert filters.do_round(2.0) == 2


def test_git_search() -> None:
    """Test that git_search matches the full commit if necessary."""
    commit_hash = "0123456789abcdef"
    repo = {commit_hash}
    prefixlen = util.git_search(repo, commit_hash)
    assert prefixlen == 16


def test_git_search_double_commit() -> None:
    """Test that git_search matches a shorter prefix length."""
    commit_hash = "0123456789abcdef"
    repo = {commit_hash[:13]}
    # Locate the shortest prefix length that matches commit_hash.
    prefixlen = util.git_search(repo, commit_hash)
    assert prefixlen == 13


@pytest.mark.asyncio
async def test_error_or_result() -> None:
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


def test_valid_homepage() -> None:
    assert util.valid_homepage("http://google.com")
    assert util.valid_homepage("https://google.com")
    assert not util.valid_homepage("http://[google.com/broken-ipv6")
    assert not util.valid_homepage("https://[google.com/broken-ipv6")

    assert not util.valid_homepage("gopher://gopher.hprc.utoronto.ca/")


def test_parse_ssh_key() -> None:
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


def test_parse_ssh_keys() -> None:
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
    assert_multiple_keys(pks)


def test_parse_ssh_keys_with_extra_lines() -> None:
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
fRSo6OFcejKc=


"""
    assert_multiple_keys(pks)


@pytest.mark.parametrize(
    "offset_str, per_page_str, expected",
    [
        ("5", "100", (5, 100)),
        ("", "100", (0, 100)),
        ("5", "", (5, 50)),
        ("", "", (0, 50)),
        ("-1", "100", (0, 100)),
        ("5", "-100", (5, 50)),
        ("0", "0", (0, 50)),
    ],
)
def test_sanitize_params(
    offset_str: str, per_page_str: str, expected: tuple[int, int]
) -> None:
    assert util.sanitize_params(offset_str, per_page_str) == expected


def assert_multiple_keys(pks) -> None:
    keys = util.parse_ssh_keys(pks)
    assert len(keys) == 2
    pfx1, key1, pfx2, key2 = pks.split()
    assert (pfx1, key1) in keys
    assert (pfx2, key2) in keys


def test_hash_query() -> None:
    # No conditions
    query = db.query(User)
    assert util.hash_query(query) == "75e76026b7d576536e745ec22892cf8f5d7b5d62"

    # With where clause
    query = db.query(User).filter(User.Username == "bla")
    assert util.hash_query(query) == "4dca710f33b1344c27ec6a3c266970f4fa6a8a00"

    # With where clause and sorting
    query = db.query(User).filter(User.Username == "bla").order_by(User.Username)
    assert util.hash_query(query) == "ee2c7846fede430776e140f8dfe1d83cd21d2eed"

    # With where clause, sorting and specific columns
    query = (
        db.query(User)
        .filter(User.Username == "bla")
        .order_by(User.Username)
        .with_entities(User.Username)
    )
    assert util.hash_query(query) == "c1db751be61443d266cf643005eee7a884dac103"
