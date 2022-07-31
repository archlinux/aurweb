from io import StringIO

from lxml import etree

parser = etree.HTMLParser()


def parse_root(html: str) -> etree.Element:
    """ Parse an lxml.etree.ElementTree root from html content.

    :param html: HTML markup
    :return: etree.Element
    """
    return etree.parse(StringIO(html), parser)


def get_errors(content: str) -> list[etree._Element]:
    root = parse_root(content)
    return root.xpath('//ul[@class="errorlist"]/li')


def get_successes(content: str) -> list[etree._Element]:
    root = parse_root(content)
    return root.xpath('//ul[@class="success"]/li')
