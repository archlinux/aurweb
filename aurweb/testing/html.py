from io import StringIO

from lxml import etree

parser = etree.HTMLParser()


def parse_root(html: str) -> etree.Element:
    """ Parse an lxml.etree.ElementTree root from html content.

    :param html: HTML markup
    :return: etree.Element
    """
    return etree.parse(StringIO(html), parser)
