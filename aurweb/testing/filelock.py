import hashlib
import os

from typing import Callable

from posix_ipc import O_CREAT, Semaphore

from aurweb import logging

logger = logging.get_logger(__name__)


def default_on_create(path):
    logger.info(f"Filelock at {path} acquired.")


class FileLock:
    def __init__(self, tmpdir, name: str):
        self.root = tmpdir
        self.path = str(self.root / name)
        self._file = str(self.root / (f"{name}.1"))

    def lock(self, on_create: Callable = default_on_create):
        hash = hashlib.sha1(self.path.encode()).hexdigest()
        with Semaphore(f"/{hash}-lock", flags=O_CREAT, initial_value=1):
            retval = os.path.exists(self._file)
            if not retval:
                with open(self._file, "w") as f:
                    f.write("1")
                on_create(self.path)

        return retval
