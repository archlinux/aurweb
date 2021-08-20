import base64
import math
import random
import re
import secrets
import string

from collections import OrderedDict
from datetime import datetime
from urllib.parse import quote_plus, urlparse
from zoneinfo import ZoneInfo

import fastapi

from email_validator import EmailNotValidError, EmailUndeliverableError, validate_email
from fastapi.responses import Response
from jinja2 import pass_context

import aurweb.config


def make_random_string(length):
    return ''.join(random.choices(string.ascii_lowercase
                                  + string.digits, k=length))


def make_nonce(length: int = 8):
    """ Generate a single random nonce. Here, token_hex generates a hex
    string of 2 hex characters per byte, where the length give is
    nbytes. This means that to get our proper string length, we need to
    cut it in half and truncate off any remaining (in the case that
    length was uneven). """
    return secrets.token_hex(math.ceil(length / 2))[:length]


def valid_username(username):
    min_len = aurweb.config.getint("options", "username_min_len")
    max_len = aurweb.config.getint("options", "username_max_len")
    if not (min_len <= len(username) <= max_len):
        return False

    # Check that username contains: one or more alphanumeric
    # characters, an optional separator of '.', '-' or '_', followed
    # by alphanumeric characters.
    return re.match(r'^[a-zA-Z0-9]+[.\-_]?[a-zA-Z0-9]+$', username)


def valid_email(email):
    try:
        validate_email(email)
    except EmailUndeliverableError:
        return False
    except EmailNotValidError:
        return False
    return True


def valid_homepage(homepage):
    parts = urlparse(homepage)
    return parts.scheme in ("http", "https") and bool(parts.netloc)


def valid_password(password):
    min_len = aurweb.config.getint("options", "passwd_min_len")
    return len(password) >= min_len


def valid_pgp_fingerprint(fp):
    fp = fp.replace(" ", "")
    try:
        # Attempt to convert the fingerprint to an int via base16.
        # If it can't, it's not a hex string.
        int(fp, 16)
    except ValueError:
        return False

    # Check the length; must be 40 hexadecimal digits.
    return len(fp) == 40


def valid_ssh_pubkey(pk):
    valid_prefixes = ("ssh-rsa", "ecdsa-sha2-nistp256",
                      "ecdsa-sha2-nistp384", "ecdsa-sha2-nistp521",
                      "ssh-ed25519")

    has_valid_prefix = False
    for prefix in valid_prefixes:
        if "%s " % prefix in pk:
            has_valid_prefix = True
            break
    if not has_valid_prefix:
        return False

    tokens = pk.strip().rstrip().split(" ")
    if len(tokens) < 2:
        return False

    return base64.b64encode(base64.b64decode(tokens[1])).decode() == tokens[1]


def migrate_cookies(request, response):
    secure_cookies = aurweb.config.getboolean("options", "disable_http_login")
    for k, v in request.cookies.items():
        response.set_cookie(k, v, secure=secure_cookies, httponly=True)
    return add_samesite_fields(response, "strict")


@pass_context
def account_url(context, user):
    request = context.get("request")
    base = f"{request.url.scheme}://{request.url.hostname}"
    if request.url.scheme == "http" and request.url.port != 80:
        base += f":{request.url.port}"
    return f"{base}/account/{user.Username}"


def timestamp_to_datetime(timestamp: int):
    return datetime.utcfromtimestamp(int(timestamp))


def as_timezone(dt: datetime, timezone: str):
    return dt.astimezone(tz=ZoneInfo(timezone))


def dedupe_qs(query_string: str, *additions):
    """ Dedupe keys found in a query string by rewriting it without
    duplicates found while iterating from the end to the beginning,
    using an ordered memo to track keys found and persist locations.

    That is, query string 'a=1&b=1&a=2' will be deduped and converted
    to 'b=1&a=2'.

    :param query_string: An HTTP URL query string.
    :param *additions: Optional additional fields to add to the query string.
    :return: Deduped query string, including *additions at the tail.
    """
    for addition in list(additions):
        query_string += f"&{addition}"

    qs = OrderedDict()
    for item in reversed(query_string.split('&')):
        key, value = item.split('=')
        if key not in qs:
            qs[key] = value
    return '&'.join([f"{k}={quote_plus(v)}" for k, v in reversed(qs.items())])


def get_vote(voteinfo, request: fastapi.Request):
    from aurweb.models.tu_vote import TUVote
    return voteinfo.tu_votes.filter(TUVote.User == request.user).first()


def number_format(value: float, places: int):
    """ A converter function similar to PHP's number_format. """
    return f"{value:.{places}f}"


def jsonify(obj):
    """ Perform a conversion on obj if it's needed. """
    if isinstance(obj, datetime):
        obj = int(obj.timestamp())
    return obj


def add_samesite_fields(response: Response, value: str):
    """ Set the SameSite field on all cookie headers found.
    Taken from https://github.com/tiangolo/fastapi/issues/1099. """
    for idx, header in enumerate(response.raw_headers):
        if header[0].decode() == "set-cookie":
            cookie = header[1].decode()
            if f"SameSite={value}" not in cookie:
                cookie += f"; SameSite={value}"
                response.raw_headers[idx] = (header[0], cookie.encode())
    return response


def get_ssh_fingerprints():
    fingerprints = {}
    fingerprint_section = aurweb.config.get_section("fingerprints")

    if fingerprint_section:
        fingerprints = {key: fingerprint_section[key] for key in fingerprint_section.keys()}

    return fingerprints
