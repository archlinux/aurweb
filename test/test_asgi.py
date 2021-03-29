import http
import os

from unittest import mock

import pytest

from fastapi import HTTPException

import aurweb.asgi
import aurweb.config


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
    response = await aurweb.asgi.http_exception_handler(None, exc)
    assert response.body.decode() == \
        f"<h1>{exc.status_code} {phrase}</h1><p>{exc.detail}</p>"
