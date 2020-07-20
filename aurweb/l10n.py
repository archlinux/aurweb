import gettext

import aurweb.config


class Translator:
    def __init__(self):
        self._localedir = aurweb.config.get('options', 'localedir')
        self._translator = {}

    def translate(self, s, lang):
        if lang == 'en':
            return s
        if lang not in self._translator:
            self._translator[lang] = gettext.translation("aurweb",
                                                         self._localedir,
                                                         languages=[lang])
        return self._translator[lang].gettext(s)


def get_translator_for_request(request):
    """
    Determine the preferred language from a FastAPI request object and build a
    translator function for it.

    Example:
    ```python
    _ = get_translator_for_request(request)
    print(_("Hello"))
    ```
    """
    lang = request.cookies.get("AURLANG")
    if lang is None:
        lang = aurweb.config.get("options", "default_lang")
    translator = Translator()

    def translate(message):
        return translator.translate(message, lang)

    return translate
