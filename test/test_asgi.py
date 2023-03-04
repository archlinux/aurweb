import http
import os
import re
from typing import Callable
from unittest import mock

import fastapi
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

import aurweb.asgi
import aurweb.aur_redis
import aurweb.config
from aurweb.exceptions import handle_form_exceptions
from aurweb.testing.requests import Request


@pytest.fixture
def setup(db_test, email_test):
    aurweb.aur_redis.redis_connection().flushall()
    yield
    aurweb.aur_redis.redis_connection().flushall()


@pytest.fixture
def mock_glab_request(monkeypatch):
    def wrapped(return_value=None, side_effect=None):
        def what_to_return(*args, **kwargs):
            if side_effect:
                return side_effect  # pragma: no cover
            return return_value

        monkeypatch.setattr("requests.post", what_to_return)

    return wrapped


def mock_glab_config(project: str = "test/project", token: str = "test-token"):
    config_get = aurweb.config.get

    def wrapper(section: str, key: str) -> str:
        if section == "notifications":
            if key == "error-project":
                return project
            elif key == "error-token":
                return token
        return config_get(section, key)

    return wrapper


@pytest.mark.asyncio
async def test_asgi_startup_session_secret_exception(monkeypatch):
    """Test that we get an IOError on app_startup when we cannot
    connect to options.redis_address."""

    redis_addr = aurweb.config.get("options", "redis_address")

    def mock_get(section: str, key: str):
        if section == "fastapi" and key == "session_secret":
            return None
        return redis_addr

    with mock.patch("aurweb.config.get", side_effect=mock_get):
        with pytest.raises(Exception):
            await aurweb.asgi.app_startup()


@pytest.mark.asyncio
async def test_asgi_startup_exception():
    # save proper session secret
    prev_secret = aurweb.asgi.session_secret

    # remove secret
    aurweb.asgi.session_secret = None

    # startup should fail
    with pytest.raises(Exception):
        await aurweb.asgi.app_startup()

    # restore previous session secret after test
    aurweb.asgi.session_secret = prev_secret


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


@pytest.mark.asyncio
async def test_asgi_app_disabled_metrics(caplog: pytest.LogCaptureFixture):
    env = {"PROMETHEUS_MULTIPROC_DIR": str()}
    with mock.patch.dict(os.environ, env):
        await aurweb.asgi.app_startup()

    expected = (
        "$PROMETHEUS_MULTIPROC_DIR is not set, the /metrics " "endpoint is disabled."
    )
    assert expected in caplog.text


@pytest.fixture
def use_traceback():
    config_getboolean = aurweb.config.getboolean

    def mock_getboolean(section: str, key: str) -> bool:
        if section == "options" and key == "traceback":
            return True
        return config_getboolean(section, key)

    with mock.patch("aurweb.config.getboolean", side_effect=mock_getboolean):
        yield


class FakeResponse:
    def __init__(self, status_code: int = 201, text: str = "{}"):
        self.status_code = status_code
        self.text = text


def test_internal_server_error_bad_glab(
    setup: None,
    use_traceback: None,
    mock_glab_request: Callable,
    caplog: pytest.LogCaptureFixture,
):
    @aurweb.asgi.app.get("/internal_server_error")
    async def internal_server_error(request: fastapi.Request):
        raise ValueError("test exception")

    with mock.patch("aurweb.config.get", side_effect=mock_glab_config()):
        with TestClient(app=aurweb.asgi.app) as request:
            mock_glab_request(FakeResponse(status_code=404))
            resp = request.get("/internal_server_error")
    assert resp.status_code == int(http.HTTPStatus.INTERNAL_SERVER_ERROR)

    expr = r"ERROR.*Unable to report exception to"
    assert re.search(expr, caplog.text)

    expr = r"FATAL\[.{7}\]"
    assert re.search(expr, caplog.text)


def test_internal_server_error_no_token(
    setup: None,
    use_traceback: None,
    mock_glab_request: Callable,
    caplog: pytest.LogCaptureFixture,
):
    @aurweb.asgi.app.get("/internal_server_error")
    async def internal_server_error(request: fastapi.Request):
        raise ValueError("test exception")

    mock_get = mock_glab_config(token="set-me")
    with mock.patch("aurweb.config.get", side_effect=mock_get):
        with TestClient(app=aurweb.asgi.app) as request:
            mock_glab_request(FakeResponse())
            resp = request.get("/internal_server_error")
    assert resp.status_code == int(http.HTTPStatus.INTERNAL_SERVER_ERROR)

    expr = r"WARNING.*Unable to report an exception found"
    assert re.search(expr, caplog.text)

    expr = r"FATAL\[.{7}\]"
    assert re.search(expr, caplog.text)


def test_internal_server_error(
    setup: None,
    use_traceback: None,
    mock_glab_request: Callable,
    caplog: pytest.LogCaptureFixture,
):
    @aurweb.asgi.app.get("/internal_server_error")
    async def internal_server_error(request: fastapi.Request):
        raise ValueError("test exception")

    with mock.patch("aurweb.config.get", side_effect=mock_glab_config()):
        with TestClient(app=aurweb.asgi.app) as request:
            mock_glab_request(FakeResponse())
            # Test with a ?query=string to cover the request.url.query path.
            resp = request.get("/internal_server_error?query=string")
    assert resp.status_code == int(http.HTTPStatus.INTERNAL_SERVER_ERROR)

    # Assert that the exception got logged with with its traceback id.
    expr = r"FATAL\[.{7}\]"
    assert re.search(expr, caplog.text)

    # Let's do it again to exercise the cached path.
    caplog.clear()
    with mock.patch("aurweb.config.get", side_effect=mock_glab_config()):
        with TestClient(app=aurweb.asgi.app) as request:
            mock_glab_request(FakeResponse())
            resp = request.get("/internal_server_error")
    assert resp.status_code == int(http.HTTPStatus.INTERNAL_SERVER_ERROR)
    assert "FATAL" not in caplog.text


def test_internal_server_error_post(
    setup: None,
    use_traceback: None,
    mock_glab_request: Callable,
    caplog: pytest.LogCaptureFixture,
):
    @aurweb.asgi.app.post("/internal_server_error")
    @handle_form_exceptions
    async def internal_server_error(request: fastapi.Request):
        raise ValueError("test exception")

    data = {"some": "data"}
    with mock.patch("aurweb.config.get", side_effect=mock_glab_config()):
        with TestClient(app=aurweb.asgi.app) as request:
            mock_glab_request(FakeResponse())
            # Test with a ?query=string to cover the request.url.query path.
            resp = request.post("/internal_server_error", data=data)
    assert resp.status_code == int(http.HTTPStatus.INTERNAL_SERVER_ERROR)

    expr = r"FATAL\[.{7}\]"
    assert re.search(expr, caplog.text)
