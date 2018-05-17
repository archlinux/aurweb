import gettext


class Translator:
    def __init__(self):
        self._translator = {}

    def translate(self, s, lang):
        if lang == 'en':
            return s
        if lang not in self._translator:
            self._translator[lang] = gettext.translation("aur",
                                                         "../../web/locale",
                                                         languages=[lang])
        self._translator[lang].install()
        return _(s)
