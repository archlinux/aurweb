import base64
import random
import re
import string

from datetime import datetime
from urllib.parse import urlparse

from email_validator import EmailNotValidError, EmailUndeliverableError, validate_email
from jinja2 import pass_context

import aurweb.config


def make_random_string(length):
    return ''.join(random.choices(string.ascii_lowercase +
                                  string.digits, k=length))


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
    for k, v in request.cookies.items():
        response.set_cookie(k, v)
    return response


@pass_context
def account_url(context, user):
    request = context.get("request")
    base = f"{request.url.scheme}://{request.url.hostname}"
    if request.url.scheme == "http" and request.url.port != 80:
        base += f":{request.url.port}"
    return f"{base}/account/{user.Username}"


def jsonify(obj):
    """ Perform a conversion on obj if it's needed. """
    if isinstance(obj, datetime):
        obj = int(obj.timestamp())
    return obj
