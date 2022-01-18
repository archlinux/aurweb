""" This module consists of aurweb's CAPTCHA utility functions and filters. """
import hashlib

from jinja2 import pass_context

from aurweb.db import query
from aurweb.models import User
from aurweb.templates import register_filter


def get_captcha_salts():
    """ Produce salts based on the current user count. """
    count = query(User).count()
    salts = []
    for i in range(0, 6):
        salts.append(f"aurweb-{count - i}")
    return salts


def get_captcha_token(salt):
    """ Produce a token for the CAPTCHA salt. """
    return hashlib.md5(salt.encode()).hexdigest()[:3]


def get_captcha_challenge(salt):
    """ Get a CAPTCHA challenge string (shell command) for a salt. """
    token = get_captcha_token(salt)
    return f"LC_ALL=C pacman -V|sed -r 's#[0-9]+#{token}#g'|md5sum|cut -c1-6"


def get_captcha_answer(token):
    """ Compute the answer via md5 of the real template text, return the
    first six digits of the hexadecimal hash. """
    text = r"""
 .--.                  Pacman v%s.%s.%s - libalpm v%s.%s.%s
/ _.-' .-.  .-.  .-.   Copyright (C) %s-%s Pacman Development Team
\  '-. '-'  '-'  '-'   Copyright (C) %s-%s Judd Vinet
 '--'
                       This program may be freely redistributed under
                       the terms of the GNU General Public License.
""" % tuple([token] * 10)
    return hashlib.md5((text + "\n").encode()).hexdigest()[:6]


@register_filter("captcha_salt")
@pass_context
def captcha_salt_filter(context):
    """ Returns the most recent CAPTCHA salt in the list of salts. """
    salts = get_captcha_salts()
    return salts[0]


@register_filter("captcha_cmdline")
@pass_context
def captcha_cmdline_filter(context, salt):
    """ Returns a CAPTCHA challenge for a given salt. """
    return get_captcha_challenge(salt)
