import configparser
import os

# Publicly visible version of aurweb. This is used to display
# aurweb versioning in the footer and must be maintained.
# Todo: Make this dynamic/automated.
AURWEB_VERSION = "v5.0.0"

_parser = None


def _get_parser():
    global _parser

    if not _parser:
        path = os.environ.get('AUR_CONFIG', '/etc/aurweb/config')
        defaults = os.environ.get('AUR_CONFIG_DEFAULTS', path + '.defaults')

        _parser = configparser.RawConfigParser()
        if os.path.isfile(defaults):
            with open(defaults) as f:
                _parser.read_file(f)
        _parser.read(path)

    return _parser


def rehash():
    """ Globally rehash the configuration parser. """
    global _parser
    _parser = None
    _get_parser()


def get_with_fallback(section, option, fallback):
    return _get_parser().get(section, option, fallback=fallback)


def get(section, option):
    return _get_parser().get(section, option)


def getboolean(section, option):
    return _get_parser().getboolean(section, option)


def getint(section, option, fallback=None):
    return _get_parser().getint(section, option, fallback=fallback)


def get_section(section_name):
    for section in _get_parser().sections():
        if section == section_name:
            return _get_parser()[section]
