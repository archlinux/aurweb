import hashlib

from aurweb import captcha


def test_captcha_salts():
    """ Make sure we can get some captcha salts. """
    salts = captcha.get_captcha_salts()
    assert len(salts) == 6


def test_captcha_token():
    """ Make sure getting a captcha salt's token matches up against
    the first three digits of the md5 hash of the salt. """
    salts = captcha.get_captcha_salts()
    salt = salts[0]

    token1 = captcha.get_captcha_token(salt)
    token2 = hashlib.md5(salt.encode()).hexdigest()[:3]

    assert token1 == token2


def test_captcha_challenge_answer():
    """ Make sure that executing the captcha challenge via shell
    produces the correct result by comparing it against a straight
    up token conversion. """
    salts = captcha.get_captcha_salts()
    salt = salts[0]

    challenge = captcha.get_captcha_challenge(salt)

    token = captcha.get_captcha_token(salt)
    challenge2 = f"LC_ALL=C pacman -V|sed -r 's#[0-9]+#{token}#g'|md5sum|cut -c1-6"

    assert challenge == challenge2


def test_captcha_salt_filter():
    """ Make sure captcha_salt_filter returns the first salt from
    get_captcha_salts().

    Example usage:
        <input type="hidden" name="captcha_salt" value="{{ captcha_salt }}">
    """
    salt = captcha.captcha_salt_filter(None)
    assert salt == captcha.get_captcha_salts()[0]


def test_captcha_cmdline_filter():
    """ Make sure that the captcha_cmdline filter gives us the
    same challenge that get_captcha_challenge does.

    Example usage:
        <code>{{ captcha_salt | captcha_cmdline }}</code>
    """
    salt = captcha.captcha_salt_filter(None)
    display1 = captcha.captcha_cmdline_filter(None, salt)
    display2 = captcha.get_captcha_challenge(salt)
    assert display1 == display2
