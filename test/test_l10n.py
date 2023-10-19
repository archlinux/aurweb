""" Test our l10n module. """
from aurweb import config, filters, l10n
from aurweb.testing.requests import Request


def test_translator():
    """Test creating l10n translation tools."""
    de_home = l10n.translator.translate("Home", "de")
    assert de_home == "Startseite"


def test_get_request_language():
    """Test getting the language setting from a request."""
    # Default language
    default_lang = config.get("options", "default_lang")
    request = Request()
    assert l10n.get_request_language(request) == default_lang

    # Language setting from cookie: de
    request.cookies["AURLANG"] = "de"
    assert l10n.get_request_language(request) == "de"

    # Language setting from cookie: nonsense
    # Should fallback to default lang
    request.cookies["AURLANG"] = "nonsense"
    assert l10n.get_request_language(request) == default_lang

    # Language setting from query param: de
    request.cookies = {}
    request.query_params = {"language": "de"}
    assert l10n.get_request_language(request) == "de"

    # Language setting from query param: nonsense
    # Should fallback to default lang
    request.query_params = {"language": "nonsense"}
    assert l10n.get_request_language(request) == default_lang

    # Language setting from query param: de and cookie
    # Query param should have precedence
    request.query_params = {"language": "de"}
    request.cookies["AURLANG"] = "fr"
    assert l10n.get_request_language(request) == "de"

    # Language setting from authenticated user
    request.cookies = {}
    request.query_params = {}
    request.user.authenticated = True
    request.user.LangPreference = "de"
    assert l10n.get_request_language(request) == "de"

    # Language setting from authenticated user with query param
    # Query param should have precedence
    request.query_params = {"language": "fr"}
    assert l10n.get_request_language(request) == "fr"

    # Language setting from authenticated user with cookie
    # DB setting should have precedence
    request.query_params = {}
    request.cookies["AURLANG"] = "fr"
    assert l10n.get_request_language(request) == "de"


def test_get_raw_translator_for_request():
    """Make sure that get_raw_translator_for_request is giving us
    the translator we expect."""
    request = Request()
    request.cookies["AURLANG"] = "de"
    translator = l10n.get_raw_translator_for_request(request)
    assert translator.gettext("Home") == l10n.translator.translate("Home", "de")


def test_get_translator_for_request():
    """Make sure that get_translator_for_request is giving us back
    our expected translation function."""
    request = Request()
    request.cookies["AURLANG"] = "de"

    translate = l10n.get_translator_for_request(request)
    assert translate("Home") == "Startseite"


def test_tn_filter():
    request = Request()
    request.cookies["AURLANG"] = "en"
    context = {"language": "en", "request": request}

    translated = filters.tn(context, 1, "%d package found.", "%d packages found.")
    assert translated == "%d package found."

    translated = filters.tn(context, 2, "%d package found.", "%d packages found.")
    assert translated == "%d packages found."
