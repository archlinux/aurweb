import configparser
import os

_parser = None


def _get_parser():
    global _parser

    if not _parser:
        _parser = configparser.RawConfigParser()
        if 'AUR_CONFIG' in os.environ:
            path = os.environ.get('AUR_CONFIG')
        else:
            path = "/etc/aurweb/config"
        _parser.read(path)

    return _parser


def get(section, option):
    return _get_parser().get(section, option)


def getboolean(section, option):
    return _get_parser().getboolean(section, option)


def getint(section, option):
    return _get_parser().getint(section, option)
