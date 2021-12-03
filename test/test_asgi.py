import http
import os

from unittest import mock

import pytest

from fastapi import HTTPException

import aurweb.asgi
import aurweb.config
import aurweb.redis

from aurweb.testing.requests import Request


@pytest.mark.asyncio
async def test_asgi_startup_session_secret_exception(monkeypatch):
    """ Test that we get an IOError on app_startup when we cannot
    connect to options.redis_address. """

    redis_addr = aurweb.config.get("options", "redis_address")

    def mock_get(section: str, key: str):
        if section == "fastapi" and key == "session_secret":
            return None
        return redis_addr

    with mock.patch("aurweb.config.get", side_effect=mock_get):
        with pytest.raises(Exception):
            await aurweb.asgi.app_startup()


@pytest.mark.asyncio
async def test_asgi_startup_exception(monkeypatch):
    with mock.patch.dict(os.environ, {"AUR_CONFIG": "conf/config.defaults"}):
        aurweb.config.rehash()
        with pytest.raises(Exception):
            await aurweb.asgi.app_startup()
    aurweb.config.rehash()


@pytest.mark.asyncio
async def test_asgi_http_exception_handler():
    exc = HTTPException(status_code=422, detail="EXCEPTION!")
    phrase = http.HTTPStatus(exc.status_code).phrase
    response = await aurweb.asgi.http_exception_handler(Request(), exc)
    assert response.status_code == 422
    content = response.body.decode()
    assert f"{exc.status_code} - {phrase}" in content
    assert "EXCEPTION!" in content


@pytest.mark.asyncio
async def test_asgi_app_unsupported_backends():
    config_get = aurweb.config.get

    # Test that the previously supported "sqlite" backend is now
    # unsupported by FastAPI.
    def mock_sqlite_backend(section: str, key: str):
        if section == "database" and key == "backend":
            return "sqlite"
        return config_get(section, key)

    with mock.patch("aurweb.config.get", side_effect=mock_sqlite_backend):
        expr = r"^.*\(sqlite\) is unsupported.*$"
        with pytest.raises(ValueError, match=expr):
            await aurweb.asgi.app_startup()
