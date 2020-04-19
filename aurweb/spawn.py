"""
Provide an automatic way of spawing an HTTP test server running aurweb.

It can be called from the command-line or from another Python module.

This module uses a global state, since you can’t open two servers with the same
configuration anyway.
"""


import atexit
import argparse
import subprocess
import sys
import time
import urllib

import aurweb.config
import aurweb.schema


children = []
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


def spawn_child(args):
    """Open a subprocess and add it to the global state."""
    if verbosity >= 1:
        print(f"Spawning {args}", file=sys.stderr)
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
    aur_location = aurweb.config.get("options", "aur_location")
    aur_location_parts = urllib.parse.urlsplit(aur_location)
    htmldir = aurweb.config.get("options", "htmldir")
    spawn_child(["php", "-S", aur_location_parts.netloc, "-t", htmldir])


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
                print(f"Sent SIGTERM to {p.args}", file=sys.stderr)
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
    start()
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        stop()
