"""
Provide an automatic way of spawing an HTTP test server running aurweb.

It can be called from the command-line or from another Python module.

This module uses a global state, since you can’t open two servers with the same
configuration anyway.
"""

import argparse
import atexit
import os
import os.path
import subprocess
import sys
import tempfile
import time
from typing import Iterable

import aurweb.config
import aurweb.schema

children = []
temporary_dir = None
verbosity = 0
asgi_backend = ""
workers = 1

FASTAPI_NGINX_PORT = int(os.environ.get("FASTAPI_NGINX_PORT", 8002))


class ProcessExceptions(Exception):
    """
    Compound exception used by stop() to list all the errors that happened when
    terminating child processes.
    """

    def __init__(self, message, exceptions):
        self.message = message
        self.exceptions = exceptions
        messages = [message] + [str(e) for e in exceptions]
        super().__init__("\n- ".join(messages))


def generate_nginx_config():
    """
    Generate an nginx configuration based on aurweb's configuration.
    The file is generated under `temporary_dir`.
    Returns the path to the created configuration file.
    """
    fastapi_bind = aurweb.config.get("fastapi", "bind_address")
    fastapi_host = fastapi_bind.split(":")[0]
    config_path = os.path.join(temporary_dir, "nginx.conf")
    with open(config_path, "w") as config:
        # We double nginx's braces because they conflict with Python's f-strings.
        config.write(
            f"""
            events {{}}
            daemon off;
            error_log /dev/stderr info;
            pid {os.path.join(temporary_dir, "nginx.pid")};
            http {{
                access_log /dev/stdout;
                client_body_temp_path {os.path.join(temporary_dir, "client_body")};
                proxy_temp_path {os.path.join(temporary_dir, "proxy")};
                fastcgi_temp_path {os.path.join(temporary_dir, "fastcgi")}1 2;
                uwsgi_temp_path {os.path.join(temporary_dir, "uwsgi")};
                scgi_temp_path {os.path.join(temporary_dir, "scgi")};
                server {{
                    listen {fastapi_host}:{FASTAPI_NGINX_PORT};
                    location / {{
                        try_files $uri @proxy_to_app;
                    }}
                    location @proxy_to_app {{
                        proxy_set_header Host $http_host;
                        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                        proxy_set_header X-Forwarded-Proto $scheme;
                        proxy_redirect off;
                        proxy_buffering off;
                        proxy_pass http://{fastapi_bind};
                    }}
                }}
            }}
        """
        )
    return config_path


def spawn_child(_args):
    """Open a subprocess and add it to the global state."""
    if verbosity >= 1:
        print(f":: Spawning {_args}", file=sys.stderr)
    children.append(subprocess.Popen(_args))


def start():
    """
    Spawn the test server. If it is already running, do nothing.

    The server can be stopped with stop(), or is automatically stopped when the
    Python process ends using atexit.
    """
    if children:
        return
    atexit.register(stop)

    if "AUR_CONFIG" in os.environ:
        os.environ["AUR_CONFIG"] = os.path.realpath(os.environ["AUR_CONFIG"])

    try:
        terminal_width = os.get_terminal_size().columns
    except OSError:
        terminal_width = 80
    print(
        "{ruler}\n"
        "Spawing FastAPI, then nginx as a reverse proxy.\n"
        "Check out {aur_location}\n"
        "Hit ^C to terminate everything.\n"
        "{ruler}".format(
            ruler=("-" * terminal_width),
            aur_location=aurweb.config.get("options", "aur_location"),
        )
    )

    # FastAPI
    fastapi_host, fastapi_port = aurweb.config.get("fastapi", "bind_address").rsplit(
        ":", 1
    )

    # Logging config.
    aurwebdir = aurweb.config.get("options", "aurwebdir")
    fastapi_log_config = os.path.join(aurwebdir, "logging.conf")

    backend_args = {
        "hypercorn": ["-b", f"{fastapi_host}:{fastapi_port}"],
        "uvicorn": ["--host", fastapi_host, "--port", fastapi_port],
        "gunicorn": [
            "--bind",
            f"{fastapi_host}:{fastapi_port}",
            "-k",
            "uvicorn.workers.UvicornWorker",
            "-w",
            str(workers),
        ],
    }
    backend_args = backend_args.get(asgi_backend)
    spawn_child(
        [
            "python",
            "-m",
            asgi_backend,
            "--log-config",
            fastapi_log_config,
        ]
        + backend_args
        + ["aurweb.asgi:app"]
    )

    # nginx
    spawn_child(["nginx", "-p", temporary_dir, "-c", generate_nginx_config()])

    print(
        f"""
 > Started nginx.
 >
 > FastAPI backend: http://{fastapi_host}:{fastapi_port}
 > FastAPI frontend: http://{fastapi_host}:{FASTAPI_NGINX_PORT}
 >
 > Frontends are hosted via nginx and should be preferred.
"""
    )


def _kill_children(_children: Iterable, exceptions=None) -> list[Exception]:
    """
    Kill each process found in `children`.

    :param _children: Iterable of child processes
    :param exceptions: Exception memo
    :return: `exceptions`
    """
    if exceptions is None:
        exceptions = []
    for p in _children:
        try:
            p.terminate()
            if verbosity >= 1:
                print(f":: Sent SIGTERM to {p.args}", file=sys.stderr)
        except Exception as e:
            exceptions.append(e)
    return exceptions


def _wait_for_children(_children: Iterable, exceptions=None) -> list[Exception]:
    """
    Wait for each process to end found in `children`.

    :param _children: Iterable of child processes
    :param exceptions: Exception memo
    :return: `exceptions`
    """
    if exceptions is None:
        exceptions = []
    for p in _children:
        try:
            rc = p.wait()
            if rc != 0 and rc != -15:
                # rc = -15 indicates the process was terminated with SIGTERM,
                # which is to be expected since we called terminate on them.
                raise Exception(f"Process {p.args} exited with {rc}")
        except Exception as e:
            exceptions.append(e)
    return exceptions


def stop() -> None:
    """
    Stop all the child processes.

    If an exception occurs during the process, the process continues anyway
    because we don’t want to leave runaway processes around, and all the
    exceptions are finally raised as a single ProcessExceptions.

    :raises: ProcessException
    :return: None
    """
    global children
    atexit.unregister(stop)
    exceptions = _kill_children(children)
    exceptions = _wait_for_children(children, exceptions)
    children = []
    if exceptions:
        raise ProcessExceptions("Errors terminating the child processes:", exceptions)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="python -m aurweb.spawn", description="Start aurweb's test server."
    )
    parser.add_argument(
        "-v", "--verbose", action="count", default=0, help="increase verbosity"
    )
    choices = ["hypercorn", "gunicorn", "uvicorn"]
    parser.add_argument(
        "-b",
        "--backend",
        choices=choices,
        default="uvicorn",
        help="asgi backend used to launch the python server",
    )
    parser.add_argument(
        "-w",
        "--workers",
        default=1,
        type=int,
        help="number of workers to use in gunicorn",
    )
    args = parser.parse_args()

    verbosity = args.verbose
    asgi_backend = args.backend
    workers = args.workers
    with tempfile.TemporaryDirectory(prefix="aurweb-") as tmpdirname:
        temporary_dir = tmpdirname
        start()
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            stop()
