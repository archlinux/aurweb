import gettext
from collections import OrderedDict

from fastapi import Request

import aurweb.config

SUPPORTED_LANGUAGES = OrderedDict(
    {
        "ar": "العربية",
        "ast": "Asturianu",
        "ca": "Català",
        "cs": "Český",
        "da": "Dansk",
        "de": "Deutsch",
        "el": "Ελληνικά",
        "en": "English",
        "es": "Español",
        "es_419": "Español (Latinoamérica)",
        "fi": "Suomi",
        "fr": "Français",
        "he": "עברית",
        "hr": "Hrvatski",
        "hu": "Magyar",
        "it": "Italiano",
        "ja": "日本語",
        "nb": "Norsk",
        "nl": "Nederlands",
        "pl": "Polski",
        "pt_BR": "Português (Brasil)",
        "pt_PT": "Português (Portugal)",
        "ro": "Română",
        "ru": "Русский",
        "sk": "Slovenčina",
        "sr": "Srpski",
        "tr": "Türkçe",
        "uk": "Українська",
        "zh_CN": "简体中文",
        "zh_TW": "正體中文",
    }
)


RIGHT_TO_LEFT_LANGUAGES = ("he", "ar")


class Translator:
    def __init__(self) -> None:
        self._localedir = aurweb.config.get("options", "localedir")
        self._translator = {}

    def get_translator(self, lang: str):
        if lang not in self._translator:
            self._translator[lang] = gettext.translation(
                "aurweb", self._localedir, languages=[lang], fallback=True
            )
        return self._translator.get(lang)

    def translate(self, s: str, lang: str):
        return self.get_translator(lang).gettext(s)


# Global translator object.
translator = Translator()


def get_request_language(request: Request) -> str:
    """Get a request's language from either query param, user setting or
    cookie. We use the configuration's [options] default_lang otherwise.

    @param request FastAPI request
    """
    request_lang = request.query_params.get("language")
    cookie_lang = request.cookies.get("AURLANG")
    if request_lang and request_lang in SUPPORTED_LANGUAGES:
        return request_lang
    elif (
        request.user.is_authenticated()
        and request.user.LangPreference in SUPPORTED_LANGUAGES
    ):
        return request.user.LangPreference
    elif cookie_lang and cookie_lang in SUPPORTED_LANGUAGES:
        return cookie_lang
    return aurweb.config.get_with_fallback("options", "default_lang", "en")


def get_raw_translator_for_request(request: Request):
    lang = get_request_language(request)
    return translator.get_translator(lang)


def get_translator_for_request(request: Request):
    """
    Determine the preferred language from a FastAPI request object and build a
    translator function for it.
    """
    lang = get_request_language(request)

    def translate(message):
        return translator.translate(message, lang)

    return translate
