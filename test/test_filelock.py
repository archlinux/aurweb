import py
from _pytest.logging import LogCaptureFixture

from aurweb.testing.filelock import FileLock


def test_filelock(tmpdir: py.path.local):
    cb_path = None

    def setup(path: str):
        nonlocal cb_path
        cb_path = str(path)

    flock = FileLock(tmpdir, "test")
    assert not flock.lock(on_create=setup)
    assert cb_path == str(tmpdir / "test")
    assert flock.lock()


def test_filelock_default(caplog: LogCaptureFixture, tmpdir: py.path.local):
    # Test default_on_create here.
    flock = FileLock(tmpdir, "test")
    assert not flock.lock()
    assert caplog.messages[0] == f"Filelock at {flock.path} acquired."
    assert flock.lock()
