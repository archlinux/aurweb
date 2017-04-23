#!/usr/bin/python3

import sys
import bleach

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

    html = get_comment(conn, commentid)
    html = html.replace('\n', '<br>')
    html = bleach.clean(html, tags=['br'])
    save_rendered_comment(conn, commentid, html)

    conn.commit()
    conn.close()


if __name__ == '__main__':
    main()
