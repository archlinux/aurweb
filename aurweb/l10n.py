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
        self._translator[lang].install()
        return _(s)
