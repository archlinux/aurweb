#!/usr/bin/env python3

import sys

import bleach
import markdown
import pygit2

import aurweb.config
import aurweb.db

repo_path = aurweb.config.get('serve', 'repo-path')
commit_uri = aurweb.config.get('options', 'commit_uri')


class LinkifyExtension(markdown.extensions.Extension):
    """
    Turn URLs into links, even without explicit markdown.
    Do not linkify URLs in code blocks.
    """

    # Captures http(s) and ftp URLs until the first non URL-ish character.
    # Excludes trailing punctuation.
    _urlre = (r'(\b(?:https?|ftp):\/\/[\w\/\#~:.?+=&%@!\-;,]+?'
              r'(?=[.:?\-;,]*(?:[^\w\/\#~:.?+=&%@!\-;,]|$)))')

    def extendMarkdown(self, md, md_globals):
        processor = markdown.inlinepatterns.AutolinkInlineProcessor(self._urlre, md)
        # Register it right after the default <>-link processor (priority 120).
        md.inlinePatterns.register(processor, 'linkify', 119)


class FlysprayLinksInlineProcessor(markdown.inlinepatterns.InlineProcessor):
    """
    Turn Flyspray task references like FS#1234 into links to bugs.archlinux.org.

    The pattern's capture group 0 is the text of the link and group 1 is the
    Flyspray task ID.
    """

    def handleMatch(self, m, data):
        el = markdown.util.etree.Element('a')
        el.set('href', f'https://bugs.archlinux.org/task/{m.group(1)}')
        el.text = markdown.util.AtomicString(m.group(0))
        return el, m.start(0), m.end(0)


class FlysprayLinksExtension(markdown.extensions.Extension):
    def extendMarkdown(self, md, md_globals):
        processor = FlysprayLinksInlineProcessor(r'\bFS#(\d+)\b', md)
        md.inlinePatterns.register(processor, 'flyspray-links', 118)


class GitCommitsInlineProcessor(markdown.inlinepatterns.InlineProcessor):
    """
    Turn Git hashes like f7f5152be5ab into links to AUR's cgit.

    Only commit references that do exist are linkified. Hashes are shortened to
    shorter non-ambiguous prefixes. Only hashes with at least 7 digits are
    considered.
    """

    def __init__(self, md, head):
        self._repo = pygit2.Repository(repo_path)
        self._head = head
        super().__init__(r'\b([0-9a-f]{7,40})\b', md)

    def handleMatch(self, m, data):
        oid = m.group(1)
        if oid not in self._repo:
            # Unkwown OID; preserve the orginal text.
            return None, None, None

        prefixlen = 12
        while prefixlen < 40:
            if oid[:prefixlen] in self._repo:
                break
            prefixlen += 1

        el = markdown.util.etree.Element('a')
        el.set('href', commit_uri % (self._head, oid[:prefixlen]))
        el.text = markdown.util.AtomicString(oid[:prefixlen])
        return el, m.start(0), m.end(0)


class GitCommitsExtension(markdown.extensions.Extension):
    _head = None

    def __init__(self, head):
        self._head = head
        super(markdown.extensions.Extension, self).__init__()

    def extendMarkdown(self, md, md_globals):
        processor = GitCommitsInlineProcessor(md, self._head)
        md.inlinePatterns.register(processor, 'git-commits', 117)


class HeadingTreeprocessor(markdown.treeprocessors.Treeprocessor):
    def run(self, doc):
        for elem in doc:
            if elem.tag == 'h1':
                elem.tag = 'h5'
            elif elem.tag in ['h2', 'h3', 'h4', 'h5']:
                elem.tag = 'h6'


class HeadingExtension(markdown.extensions.Extension):
    def extendMarkdown(self, md, md_globals):
        # Priority doesn't matter since we don't conflict with other processors.
        md.treeprocessors.register(HeadingTreeprocessor(md), 'heading', 30)


def get_comment(conn, commentid):
    cur = conn.execute('SELECT PackageComments.Comments, PackageBases.Name '
                       'FROM PackageComments INNER JOIN PackageBases '
                       'ON PackageBases.ID = PackageComments.PackageBaseID '
                       'WHERE PackageComments.ID = ?', [commentid])
    return cur.fetchone()


def save_rendered_comment(conn, commentid, html):
    conn.execute('UPDATE PackageComments SET RenderedComment = ? WHERE ID = ?',
                 [html, commentid])


def main():
    commentid = int(sys.argv[1])

    conn = aurweb.db.Connection()

    text, pkgbase = get_comment(conn, commentid)
    html = markdown.markdown(text, extensions=['fenced_code',
                                               LinkifyExtension(),
                                               FlysprayLinksExtension(),
                                               GitCommitsExtension(pkgbase),
                                               HeadingExtension()])
    allowed_tags = (bleach.sanitizer.ALLOWED_TAGS +
                    ['p', 'pre', 'h4', 'h5', 'h6', 'br', 'hr'])
    html = bleach.clean(html, tags=allowed_tags)
    save_rendered_comment(conn, commentid, html)

    conn.commit()
    conn.close()


if __name__ == '__main__':
    main()
