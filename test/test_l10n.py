""" Test our l10n module. """
from aurweb import l10n
from aurweb.testing.requests import Request


def test_translator():
    """ Test creating l10n translation tools. """
    de_home = l10n.translator.translate("Home", "de")
    assert de_home == "Startseite"


def test_get_request_language():
    """ First, tests default_lang, then tests a modified AURLANG cookie. """
    request = Request()
    assert l10n.get_request_language(request) == "en"

    request.cookies["AURLANG"] = "de"
    assert l10n.get_request_language(request) == "de"


def test_get_raw_translator_for_request():
    """ Make sure that get_raw_translator_for_request is giving us
    the translator we expect. """
    request = Request()
    request.cookies["AURLANG"] = "de"
    translator = l10n.get_raw_translator_for_request(request)
    assert translator.gettext("Home") == \
        l10n.translator.translate("Home", "de")


def test_get_translator_for_request():
    """ Make sure that get_translator_for_request is giving us back
    our expected translation function. """
    request = Request()
    request.cookies["AURLANG"] = "de"

    translate = l10n.get_translator_for_request(request)
    assert translate("Home") == "Startseite"
