#!/usr/bin/python3

import sys
import bleach
import markdown

import aurweb.db


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
    html = markdown.markdown(text, extensions=['nl2br'])
    allowed_tags = bleach.sanitizer.ALLOWED_TAGS + ['p', 'br']
    html = bleach.clean(html, tags=allowed_tags)
    save_rendered_comment(conn, commentid, html)

    conn.commit()
    conn.close()


if __name__ == '__main__':
    main()
