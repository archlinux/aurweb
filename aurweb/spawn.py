"""
Provide an automatic way of spawing an HTTP test server running aurweb.

It can be called from the command-line or from another Python module.

This module uses a global state, since you can’t open two servers with the same
configuration anyway.
"""


import atexit
import argparse
import os
import subprocess
import sys
import tempfile
import time
import urllib

import aurweb.config
import aurweb.schema


children = []
temporary_dir = None
verbosity = 0


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
    aur_location = aurweb.config.get("options", "aur_location")
    aur_location_parts = urllib.parse.urlsplit(aur_location)
    config_path = os.path.join(temporary_dir, "nginx.conf")
    config = open(config_path, "w")
    # We double nginx's braces because they conflict with Python's f-strings.
    config.write(f"""
        events {{}}
        daemon off;
        error_log /dev/stderr info;
        pid {os.path.join(temporary_dir, "nginx.pid")};
        http {{
            access_log /dev/stdout;
            server {{
                listen {aur_location_parts.netloc};
                location / {{
                    proxy_pass http://{aurweb.config.get("php", "bind_address")};
                }}
                location /hello {{
                    proxy_pass http://{aurweb.config.get("fastapi", "bind_address")};
                }}
            }}
        }}
    """)
    return config_path


def spawn_child(args):
    """Open a subprocess and add it to the global state."""
    if verbosity >= 1:
        print(f":: Spawning {args}", file=sys.stderr)
    children.append(subprocess.Popen(args))


def start():
    """
    Spawn the test server. If it is already running, do nothing.

    The server can be stopped with stop(), or is automatically stopped when the
    Python process ends using atexit.
    """
    if children:
        return
    atexit.register(stop)

    print("{ruler}\n"
          "Spawing PHP and FastAPI, then nginx as a reverse proxy.\n"
          "Check out {aur_location}\n"
          "Hit ^C to terminate everything.\n"
          "{ruler}"
          .format(ruler=("-" * os.get_terminal_size().columns),
                  aur_location=aurweb.config.get('options', 'aur_location')))

    # PHP
    php_address = aurweb.config.get("php", "bind_address")
    htmldir = aurweb.config.get("php", "htmldir")
    spawn_child(["php", "-S", php_address, "-t", htmldir])

    # FastAPI
    host, port = aurweb.config.get("fastapi", "bind_address").rsplit(":", 1)
    spawn_child(["python", "-m", "uvicorn",
                 "--host", host,
                 "--port", port,
                 "aurweb.asgi:app"])

    # nginx
    spawn_child(["nginx", "-p", temporary_dir, "-c", generate_nginx_config()])


def stop():
    """
    Stop all the child processes.

    If an exception occurs during the process, the process continues anyway
    because we don’t want to leave runaway processes around, and all the
    exceptions are finally raised as a single ProcessExceptions.
    """
    global children
    atexit.unregister(stop)
    exceptions = []
    for p in children:
        try:
            p.terminate()
            if verbosity >= 1:
                print(f":: Sent SIGTERM to {p.args}", file=sys.stderr)
        except Exception as e:
            exceptions.append(e)
    for p in children:
        try:
            rc = p.wait()
            if rc != 0 and rc != -15:
                # rc = -15 indicates the process was terminated with SIGTERM,
                # which is to be expected since we called terminate on them.
                raise Exception(f"Process {p.args} exited with {rc}")
        except Exception as e:
            exceptions.append(e)
    children = []
    if exceptions:
        raise ProcessExceptions("Errors terminating the child processes:",
                                exceptions)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='python -m aurweb.spawn',
        description='Start aurweb\'s test server.')
    parser.add_argument('-v', '--verbose', action='count', default=0,
                        help='increase verbosity')
    args = parser.parse_args()
    verbosity = args.verbose
    with tempfile.TemporaryDirectory(prefix="aurweb-") as tmpdirname:
        temporary_dir = tmpdirname
        start()
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            stop()
