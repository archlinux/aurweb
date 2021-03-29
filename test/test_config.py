from aurweb import config


def test_get():
    assert config.get("options", "disable_http_login") == "0"


def test_getboolean():
    assert not config.getboolean("options", "disable_http_login")


def test_getint():
    assert config.getint("options", "disable_http_login") == 0
