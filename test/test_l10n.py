""" Test our l10n module. """
from aurweb import l10n


class FakeRequest:
    """ A fake Request doppleganger; use this to change request.cookies
    easily and with no side-effects. """

    def __init__(self, *args, **kwargs):
        self.cookies = kwargs.pop("cookies", dict())


def test_translator():
    """ Test creating l10n translation tools. """
    de_home = l10n.translator.translate("Home", "de")
    assert de_home == "Startseite"


def test_get_request_language():
    """ First, tests default_lang, then tests a modified AURLANG cookie. """
    request = FakeRequest()
    assert l10n.get_request_language(request) == "en"

    request.cookies["AURLANG"] = "de"
    assert l10n.get_request_language(request) == "de"


def test_get_raw_translator_for_request():
    """ Make sure that get_raw_translator_for_request is giving us
    the translator we expect. """
    request = FakeRequest(cookies={"AURLANG": "de"})

    translator = l10n.get_raw_translator_for_request(request)
    assert translator.gettext("Home") == \
        l10n.translator.translate("Home", "de")


def test_get_translator_for_request():
    """ Make sure that get_translator_for_request is giving us back
    our expected translation function. """
    request = FakeRequest(cookies={"AURLANG": "de"})

    translate = l10n.get_translator_for_request(request)
    assert translate("Home") == "Startseite"
