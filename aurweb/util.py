import math
import re
import secrets
import shlex
import string
from datetime import datetime
from hashlib import sha1
from http import HTTPStatus
from subprocess import PIPE, Popen
from typing import Callable, Iterable, Tuple, Union
from urllib.parse import urlparse

import fastapi
import pygit2
from email_validator import EmailSyntaxError, validate_email
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Query

import aurweb.config
from aurweb import aur_logging, defaults

logger = aur_logging.get_logger(__name__)


def make_random_string(length: int) -> str:
    alphanumerics = string.ascii_lowercase + string.digits
    return "".join([secrets.choice(alphanumerics) for i in range(length)])


def make_nonce(length: int = 8):
    """Generate a single random nonce. Here, token_hex generates a hex
    string of 2 hex characters per byte, where the length give is
    nbytes. This means that to get our proper string length, we need to
    cut it in half and truncate off any remaining (in the case that
    length was uneven)."""
    return secrets.token_hex(math.ceil(length / 2))[:length]


def valid_username(username):
    min_len = aurweb.config.getint("options", "username_min_len")
    max_len = aurweb.config.getint("options", "username_max_len")
    if not (min_len <= len(username) <= max_len):
        return False

    # Check that username contains: one or more alphanumeric
    # characters, an optional separator of '.', '-' or '_', followed
    # by alphanumeric characters.
    return re.match(r"^[a-zA-Z0-9]+[.\-_]?[a-zA-Z0-9]+$", username)


def valid_email(email):
    try:
        validate_email(email, check_deliverability=False)
    except EmailSyntaxError:
        return False
    return True


def valid_homepage(homepage):
    try:
        parts = urlparse(homepage)
    except ValueError:
        return False
    return parts.scheme in ("http", "https") and bool(parts.netloc)


def valid_password(password):
    min_len = aurweb.config.getint("options", "passwd_min_len")
    return len(password) >= min_len


def valid_pgp_fingerprint(fp):
    try:
        # Attempt to convert the fingerprint to an int via base16.
        # If it can't, it's not a hex string.
        int(fp, 16)
    except ValueError:
        return False

    # Check the length; must be 40 hexadecimal digits.
    return len(fp) == 40


def jsonify(obj):
    """Perform a conversion on obj if it's needed."""
    if isinstance(obj, datetime):
        obj = int(obj.timestamp())
    return obj


def get_ssh_fingerprints():
    return aurweb.config.get_section("fingerprints") or {}


def apply_all(iterable: Iterable, fn: Callable):
    for item in iterable:
        fn(item)
    return iterable


def sanitize_params(offset_str: str, per_page_str: str) -> Tuple[int, int]:
    try:
        offset = defaults.O if int(offset_str) < 0 else int(offset_str)
    except ValueError:
        offset = defaults.O

    try:
        per_page = defaults.PP if int(per_page_str) <= 0 else int(per_page_str)
    except ValueError:
        per_page = defaults.PP

    return offset, per_page


def strtobool(value: Union[str, bool]) -> bool:
    if not value:
        return False
    return str(value).lower() in ("y", "yes", "t", "true", "on", "1")


def file_hash(filepath: str, hash_function: Callable) -> str:
    """
    Return a hash of filepath contents using `hash_function`.

    `hash_function` can be any one of the hashlib module's hash
    functions which implement the `hexdigest()` method -- e.g.
    hashlib.sha1, hashlib.md5, etc.

    :param filepath: Path to file you want to hash
    :param hash_function: hashlib hash function
    :return: hash_function(filepath_content).hexdigest()
    """
    with open(filepath, "rb") as f:
        hash_ = hash_function(f.read())
    return hash_.hexdigest()


def git_search(repo: pygit2.Repository, commit_hash: str) -> int:
    """
    Return the shortest prefix length matching `commit_hash` found.

    :param repo: pygit2.Repository instance
    :param commit_hash: Full length commit hash
    :return: Shortest unique prefix length found
    """
    prefixlen = 12
    while prefixlen < len(commit_hash):
        if commit_hash[:prefixlen] in repo:
            break
        prefixlen += 1
    return prefixlen


async def error_or_result(next: Callable, *args, **kwargs) -> fastapi.Response:
    """
    Try to return a response from `next`.

    If RuntimeError is raised during next(...) execution, return a
    500 with the exception's error as a JSONResponse.

    :param next: Callable of the next fastapi route callback
    :param *args: Variable number of arguments passed to the endpoint
    :param **kwargs: Optional kwargs to pass to the endpoint
    :return: next(...) retval; if an exc is raised: a 500 response
    """
    try:
        response = await next(*args, **kwargs)
    except RuntimeError as exc:
        logger.error("RuntimeError: %s", exc)
        status_code = HTTPStatus.INTERNAL_SERVER_ERROR
        return JSONResponse({"error": str(exc)}, status_code=status_code)
    return response


def parse_ssh_key(string: str) -> Tuple[str, str]:
    """Parse an SSH public key."""
    invalid_exc = ValueError("The SSH public key is invalid.")
    parts = re.sub(r"\s\s+", " ", string.strip()).split()
    if len(parts) < 2:
        raise invalid_exc

    prefix, key = parts[:2]
    prefixes = set(aurweb.config.get("auth", "valid-keytypes").split(" "))
    if prefix not in prefixes:
        raise invalid_exc

    proc = Popen(["ssh-keygen", "-l", "-f", "-"], stdin=PIPE, stdout=PIPE, stderr=PIPE)
    out, _ = proc.communicate(f"{prefix} {key}".encode())
    if proc.returncode:
        raise invalid_exc

    return prefix, key


def parse_ssh_keys(string: str) -> set[Tuple[str, str]]:
    """Parse a list of SSH public keys."""
    return {parse_ssh_key(e) for e in string.strip().splitlines(True) if e.strip()}


def shell_exec(cmdline: str, cwd: str) -> Tuple[int, str, str]:
    args = shlex.split(cmdline)
    proc = Popen(args, cwd=cwd, stdout=PIPE, stderr=PIPE)
    out, err = proc.communicate()
    return proc.returncode, out.decode().strip(), err.decode().strip()


def hash_query(query: Query):
    return sha1(
        str(query.statement.compile(compile_kwargs={"literal_binds": True})).encode()
    ).hexdigest()


def get_client_ip(request: fastapi.Request) -> str:
    """
    Returns the client's IP address for a Request.
    Falls back to 'testclient' if request.client is None
    """
    return request.client.host if request.client else "testclient"
