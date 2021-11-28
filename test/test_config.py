import configparser
import io
import os
import re

from unittest import mock

from aurweb import config
from aurweb.scripts.config import main


def noop(*args, **kwargs) -> None:
    return


def test_get():
    assert config.get("options", "disable_http_login") == "0"


def test_getboolean():
    assert not config.getboolean("options", "disable_http_login")


def test_getint():
    assert config.getint("options", "disable_http_login") == 0


def mock_config_get():
    config_get = config.get

    def _mock_config_get(section: str, option: str):
        if section == "options":
            if option == "salt_rounds":
                return "666"
        return config_get(section, option)
    return _mock_config_get


@mock.patch("aurweb.config.get", side_effect=mock_config_get())
def test_config_main_get(get: str):
    stdout = io.StringIO()
    args = ["aurweb-config", "get", "options", "salt_rounds"]
    with mock.patch("sys.argv", args):
        with mock.patch("sys.stdout", stdout):
            main()

    expected = "666"
    assert stdout.getvalue().strip() == expected


@mock.patch("aurweb.config.get", side_effect=mock_config_get())
def test_config_main_get_unknown_section(get: str):
    stderr = io.StringIO()
    args = ["aurweb-config", "get", "fakeblahblah", "salt_rounds"]
    with mock.patch("sys.argv", args):
        with mock.patch("sys.stderr", stderr):
            main()

    # With an invalid section, we should get a usage error.
    expected = r'^error: no section found$'
    assert re.match(expected, stderr.getvalue().strip())


@mock.patch("aurweb.config.get", side_effect=mock_config_get())
def test_config_main_get_unknown_option(get: str):
    stderr = io.StringIO()
    args = ["aurweb-config", "get", "options", "fakeblahblah"]
    with mock.patch("sys.argv", args):
        with mock.patch("sys.stderr", stderr):
            main()

    expected = "error: no option found"
    assert stderr.getvalue().strip() == expected


@mock.patch("aurweb.config.save", side_effect=noop)
def test_config_main_set(save: None):
    data = None

    def mock_replace_key(section: str, option: str, value: str) -> None:
        nonlocal data
        data = value

    args = ["aurweb-config", "set", "options", "salt_rounds", "666"]
    with mock.patch("sys.argv", args):
        with mock.patch("aurweb.config.replace_key",
                        side_effect=mock_replace_key):
            main()

    expected = "666"
    assert data == expected


def test_config_main_set_immutable():
    data = None

    def mock_replace_key(section: str, option: str, value: str) -> None:
        nonlocal data
        data = value

    args = ["aurweb-config", "set", "options", "salt_rounds", "666"]
    with mock.patch.dict(os.environ, {"AUR_CONFIG_IMMUTABLE": "1"}):
        with mock.patch("sys.argv", args):
            with mock.patch("aurweb.config.replace_key",
                            side_effect=mock_replace_key):
                main()

    expected = None
    assert data == expected


def test_config_main_set_invalid_value():
    stderr = io.StringIO()

    args = ["aurweb-config", "set", "options", "salt_rounds"]
    with mock.patch("sys.argv", args):
        with mock.patch("sys.stderr", stderr):
            main()

    expected = "error: no value provided"
    assert stderr.getvalue().strip() == expected


@mock.patch("aurweb.config.save", side_effect=noop)
def test_config_main_set_unknown_section(save: None):
    stderr = io.StringIO()

    def mock_replace_key(section: str, option: str, value: str) -> None:
        raise configparser.NoSectionError(section=section)

    args = ["aurweb-config", "set", "options", "salt_rounds", "666"]
    with mock.patch("sys.argv", args):
        with mock.patch("sys.stderr", stderr):
            with mock.patch("aurweb.config.replace_key",
                            side_effect=mock_replace_key):
                main()

    assert stderr.getvalue().strip() == "error: no section found"
