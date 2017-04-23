#!/usr/bin/python3

import re
import sys
import bleach
import markdown

import aurweb.db


class LinkifyPreprocessor(markdown.preprocessors.Preprocessor):
    _urlre = re.compile(r'(\b(?:https?|ftp):\/\/[\w\/\#~:.?+=&%@!\-;,]+?'
                        r'(?=[.:?\-;,]*(?:[^\w\/\#~:.?+=&%@!\-;,]|$)))')

    def run(self, lines):
        return [self._urlre.sub(r'<\1>', line) for line in lines]


class LinkifyExtension(markdown.extensions.Extension):
    def extendMarkdown(self, md, md_globals):
        md.preprocessors.add('linkify', LinkifyPreprocessor(md), '_end')


def get_comment(conn, commentid):
    cur = conn.execute('SELECT Comments FROM PackageComments WHERE ID = ?',
                       [commentid])
    return cur.fetchone()[0]


def save_rendered_comment(conn, commentid, html):
    conn.execute('UPDATE PackageComments SET RenderedComment = ? WHERE ID = ?',
                 [html, commentid])


def main():
    commentid = int(sys.argv[1])

    conn = aurweb.db.Connection()

    text = get_comment(conn, commentid)
    html = markdown.markdown(text, extensions=['nl2br', LinkifyExtension()])
    allowed_tags = bleach.sanitizer.ALLOWED_TAGS + ['p', 'br']
    html = bleach.clean(html, tags=allowed_tags)
    save_rendered_comment(conn, commentid, html)

    conn.commit()
    conn.close()


if __name__ == '__main__':
    main()
