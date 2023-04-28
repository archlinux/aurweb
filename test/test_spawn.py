import os
import tempfile
from typing import Tuple
from unittest import mock

import pytest

import aurweb.config
import aurweb.spawn

# Some os.environ overrides we use in this suite.
TEST_ENVIRONMENT = {"FASTAPI_NGINX_PORT": "8002"}


class FakeProcess:
    """Fake a subprocess.Popen return object."""

    returncode = 0
    stdout = b""
    stderr = b""

    def __init__(self, *args, **kwargs):
        """We need this constructor to remain compatible with Popen."""

    def communicate(self) -> Tuple[bytes, bytes]:
        return self.stdout, self.stderr

    def terminate(self) -> None:
        raise Exception("Fake termination.")

    def wait(self) -> int:
        return self.returncode


class MockFakeProcess:
    """FakeProcess construction helper to be used in mocks."""

    def __init__(self, return_code: int = 0, stdout: bytes = b"", stderr: bytes = b""):
        self.returncode = return_code
        self.stdout = stdout
        self.stderr = stderr

    def process(self, *args, **kwargs) -> FakeProcess:
        proc = FakeProcess()
        proc.returncode = self.returncode
        proc.stdout = self.stdout
        proc.stderr = self.stderr
        return proc


@mock.patch.dict("os.environ", TEST_ENVIRONMENT)
def test_spawn_generate_nginx_config():
    ctx = tempfile.TemporaryDirectory()
    with ctx and mock.patch("aurweb.spawn.temporary_dir", ctx.name):
        aurweb.spawn.generate_nginx_config()
        nginx_config_path = os.path.join(ctx.name, "nginx.conf")
        with open(nginx_config_path) as f:
            nginx_config = f.read().rstrip()

    fastapi_address = aurweb.config.get("fastapi", "bind_address")
    fastapi_host = fastapi_address.split(":")[0]
    expected_content = [
        f'listen {fastapi_host}:{TEST_ENVIRONMENT.get("FASTAPI_NGINX_PORT")}',
        f"proxy_pass http://{fastapi_address}",
    ]
    for expected in expected_content:
        assert expected in nginx_config


@mock.patch("aurweb.spawn.asgi_backend", "uvicorn")
@mock.patch("aurweb.spawn.verbosity", 1)
@mock.patch("aurweb.spawn.workers", 1)
def test_spawn_start_stop():
    ctx = tempfile.TemporaryDirectory()
    with ctx and mock.patch("aurweb.spawn.temporary_dir", ctx.name):
        aurweb.spawn.start()
        aurweb.spawn.stop()


@mock.patch("aurweb.spawn.asgi_backend", "uvicorn")
@mock.patch("aurweb.spawn.verbosity", 1)
@mock.patch("aurweb.spawn.workers", 1)
@mock.patch("aurweb.spawn.children", [MockFakeProcess().process()])
def test_spawn_start_noop_with_children():
    aurweb.spawn.start()


@mock.patch("aurweb.spawn.asgi_backend", "uvicorn")
@mock.patch("aurweb.spawn.verbosity", 1)
@mock.patch("aurweb.spawn.workers", 1)
@mock.patch("aurweb.spawn.children", [MockFakeProcess().process()])
def test_spawn_stop_terminate_failure():
    ctx = tempfile.TemporaryDirectory()
    with ctx and mock.patch("aurweb.spawn.temporary_dir", ctx.name):
        match = r"^Errors terminating the child processes"
        with pytest.raises(aurweb.spawn.ProcessExceptions, match=match):
            aurweb.spawn.stop()


@mock.patch("aurweb.spawn.asgi_backend", "uvicorn")
@mock.patch("aurweb.spawn.verbosity", 1)
@mock.patch("aurweb.spawn.workers", 1)
@mock.patch("aurweb.spawn.children", [MockFakeProcess(1).process()])
def test_spawn_stop_wait_failure():
    ctx = tempfile.TemporaryDirectory()
    with ctx and mock.patch("aurweb.spawn.temporary_dir", ctx.name):
        match = r"^Errors terminating the child processes"
        with pytest.raises(aurweb.spawn.ProcessExceptions, match=match):
            aurweb.spawn.stop()
