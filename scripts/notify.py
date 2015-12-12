#!/usr/bin/python3

import configparser
import email.mime.text
import mysql.connector
import os
import smtplib
import subprocess
import sys
import textwrap

config = configparser.RawConfigParser()
config.read(os.path.dirname(os.path.realpath(__file__)) + '/../conf/config')

aur_db_host = config.get('database', 'host')
aur_db_name = config.get('database', 'name')
aur_db_user = config.get('database', 'user')
aur_db_pass = config.get('database', 'password')
aur_db_socket = config.get('database', 'socket')

aur_location = config.get('options', 'aur_location')
aur_request_ml = config.get('options', 'aur_request_ml')

sendmail = config.get('notifications', 'sendmail')
sender = config.get('notifications', 'sender')
reply_to = config.get('notifications', 'reply-to')


def headers_cc(cclist):
    return {'Cc': str.join(', ', cclist)}

def headers_msgid(thread_id):
    return {'Message-ID': thread_id}

def headers_reply(thread_id):
    return {'In-Reply-To': thread_id, 'References': thread_id}

def send_notification(to, subject, body, refs, headers={}):
    body = '\n'.join([textwrap.fill(line) for line in body.splitlines()])
    body += '\n\n' + refs

    for recipient in to:
        msg = email.mime.text.MIMEText(body, 'plain', 'utf-8')
        msg['Subject'] = subject
        msg['From'] = sender
        msg['Reply-to'] = reply_to
        msg['To'] = recipient

        for key, value in headers.items():
            msg[key] = value

        p = subprocess.Popen([sendmail, '-t', '-oi'], stdin=subprocess.PIPE)
        p.communicate(msg.as_bytes())

def username_from_id(cur, uid):
    cur.execute('SELECT UserName FROM Users WHERE ID = %s', [uid])
    return cur.fetchone()[0]

def pkgbase_from_id(cur, pkgbase_id):
    cur.execute('SELECT Name FROM PackageBases WHERE ID = %s', [pkgbase_id])
    return cur.fetchone()[0]

def pkgbase_from_pkgreq(cur, reqid):
    cur.execute('SELECT PackageBaseID FROM PackageRequests WHERE ID = %s',
                [reqid])
    return cur.fetchone()[0]

def get_user_email(cur, uid):
    cur.execute('SELECT Email FROM Users WHERE ID = %s', [uid])
    return cur.fetchone()[0]

def get_maintainer_email(cur, pkgbase_id):
    cur.execute('SELECT Users.Email FROM Users ' +
                'INNER JOIN PackageBases ' +
                'ON PackageBases.MaintainerUID = Users.ID WHERE ' +
                'PackageBases.ID = %s', [pkgbase_id])
    return cur.fetchone()[0]

def get_recipients(cur, pkgbase_id, uid):
    cur.execute('SELECT DISTINCT Users.Email FROM Users ' +
                'INNER JOIN CommentNotify ' +
                'ON CommentNotify.UserID = Users.ID WHERE ' +
                'CommentNotify.UserID != %s AND ' +
                'CommentNotify.PackageBaseID = %s', [uid, pkgbase_id])
    return [row[0] for row in cur.fetchall()]

def get_request_recipients(cur, pkgbase_id, uid):
    cur.execute('SELECT DISTINCT Users.Email FROM Users ' +
                'INNER JOIN PackageBases ' +
                'ON PackageBases.MaintainerUID = Users.ID WHERE ' +
                'Users.ID = %s OR PackageBases.ID = %s', [uid, pkgbase_id])
    return [row[0] for row in cur.fetchall()]

def get_comment(cur, comment_id):
    cur.execute('SELECT Comments FROM PackageComments WHERE ID = %s',
                [comment_id])
    return cur.fetchone()[0]

def get_flagger_comment(cur, pkgbase_id):
    cur.execute('SELECT FlaggerComment FROM PackageBases WHERE ID = %s',
                [pkgbase_id])
    return cur.fetchone()[0]

def get_request_comment(cur, reqid):
    cur.execute('SELECT Comments FROM PackageRequests WHERE ID = %s', [reqid])
    return cur.fetchone()[0]

def get_request_closure_comment(cur, reqid):
    cur.execute('SELECT ClosureComment FROM PackageRequests WHERE ID = %s',
                [reqid])
    return cur.fetchone()[0]

def send_resetkey(cur, uid):
    cur.execute('SELECT UserName, Email, ResetKey FROM Users WHERE ID = %s',
                [uid])
    username, to, resetkey = cur.fetchone()

    subject = 'AUR Password Reset'
    body = 'A password reset request was submitted for the account %s ' \
           'associated with your email address. If you wish to reset your ' \
           'password follow the link [1] below, otherwise ignore this ' \
           'message and nothing will happen.' % (username)
    refs = '[1] ' + aur_location + '/passreset/?resetkey=' + resetkey

    send_notification([to], subject, body, refs)

def welcome(cur, uid):
    cur.execute('SELECT UserName, Email, ResetKey FROM Users WHERE ID = %s',
                [uid])
    username, to, resetkey = cur.fetchone()

    subject = 'Welcome to the Arch User Repository'
    body = 'Welcome to the Arch User Repository! In order to set an initial ' \
           'password for your new account, please click the link [1] below. ' \
           'If the link does not work, try copying and pasting it into your ' \
           'browser.'
    refs = '[1] ' + aur_location + '/passreset/?resetkey=' + resetkey

    send_notification([to], subject, body, refs)

def comment(cur, uid, pkgbase_id, comment_id):
    user = username_from_id(cur, uid)
    pkgbase = pkgbase_from_id(cur, pkgbase_id)
    to = get_recipients(cur, pkgbase_id, uid)
    text = get_comment(cur, comment_id)

    uri = aur_location + '/pkgbase/' + pkgbase + '/'

    user_uri = aur_location + '/account/' + user + '/'
    pkgbase_uri = aur_location + '/pkgbase/' + pkgbase + '/'

    subject = 'AUR Comment for %s' % (pkgbase)
    body = '%s [1] added the following comment to %s [2]:' % (user, pkgbase)
    body += '\n\n' + text + '\n\n'
    body += 'If you no longer wish to receive notifications about this ' \
            'package, please go to the package page [2] and select "%s".' % \
            ('Disable notifications')
    refs = '[1] ' + user_uri + '\n'
    refs += '[2] ' + pkgbase_uri
    thread_id = '<pkg-notifications-' + pkgbase + '@aur.archlinux.org>'
    headers = headers_reply(thread_id)

    send_notification(to, subject, body, refs, headers)

def flag(cur, uid, pkgbase_id):
    user = username_from_id(cur, uid)
    pkgbase = pkgbase_from_id(cur, pkgbase_id)
    to = [get_maintainer_email(cur, pkgbase_id)]
    text = get_flagger_comment(cur, pkgbase_id)

    user_uri = aur_location + '/account/' + user + '/'
    pkgbase_uri = aur_location + '/pkgbase/' + pkgbase + '/'

    subject = 'AUR Out-of-date Notification for %s' % (pkgbase)
    body = 'Your package %s [1] has been flagged out-of-date by %s [2]:' % \
           (pkgbase, user)
    body += '\n\n' + text
    refs = '[1] ' + pkgbase_uri + '\n'
    refs += '[2] ' + user_uri

    send_notification(to, subject, body, refs)

def comaintainer_add(cur, pkgbase_id, uid):
    pkgbase = pkgbase_from_id(cur, pkgbase_id)
    to = [get_user_email(cur, uid)]

    pkgbase_uri = aur_location + '/pkgbase/' + pkgbase + '/'

    subject = 'AUR Co-Maintainer Notification for %s' % (pkgbase)
    body = 'You were added to the co-maintainer list of %s [1].' % (pkgbase)
    refs = '[1] ' + pkgbase_uri + '\n'

    send_notification(to, subject, body, refs)

def comaintainer_remove(cur, pkgbase_id, uid):
    pkgbase = pkgbase_from_id(cur, pkgbase_id)
    to = [get_user_email(cur, uid)]

    pkgbase_uri = aur_location + '/pkgbase/' + pkgbase + '/'

    subject = 'AUR Co-Maintainer Notification for %s' % (pkgbase)
    body = 'You were removed from the co-maintainer list of %s [1].' % \
            (pkgbase)
    refs = '[1] ' + pkgbase_uri + '\n'

    send_notification(to, subject, body, refs)

def delete(cur, uid, old_pkgbase_id, new_pkgbase_id=None):
    user = username_from_id(cur, uid)
    old_pkgbase = pkgbase_from_id(cur, old_pkgbase_id)
    if new_pkgbase_id:
        new_pkgbase = pkgbase_from_id(cur, new_pkgbase_id)
    to = get_recipients(cur, old_pkgbase_id, uid)

    user_uri = aur_location + '/account/' + user + '/'
    pkgbase_uri = aur_location + '/pkgbase/' + pkgbase + '/'

    subject = 'AUR Package deleted: %s' % (old_pkgbase)
    if new_pkgbase_id:
        new_pkgbase_uri = aur_location + '/pkgbase/' + new_pkgbase + '/'
        body = '%s [1] merged %s [2] into %s [3].\n\n' \
               'If you no longer wish receive notifications about the new ' \
               'package, please go to [3] and click "%s".' %\
               (user, old_pkgbase, new_pkgbase, 'Disable notifications')
        refs = '[1] ' + user_uri + '\n'
        refs += '[2] ' + pkgbase_uri + '\n'
        refs += '[3] ' + new_pkgbase_uri
    else:
        body = '%s [1] deleted %s [2].\n\n' \
               'You will no longer receive notifications about this ' \
               'package.' % (user, old_pkgbase)
        refs = '[1] ' + user_uri + '\n'
        refs += '[2] ' + pkgbase_uri

    send_notification(to, subject, body, refs)

def request_open(cur, uid, reqid, reqtype, pkgbase_id, merge_into=None):
    user = username_from_id(cur, uid)
    pkgbase = pkgbase_from_id(cur, pkgbase_id)
    to = [aur_request_ml]
    cc = get_request_recipients(cur, pkgbase_id, uid)
    text = get_request_comment(cur, reqid)

    user_uri = aur_location + '/account/' + user + '/'
    pkgbase_uri = aur_location + '/pkgbase/' + pkgbase + '/'

    subject = '[PRQ#%d] %s Request for %s' % \
              (int(reqid), reqtype.title(), pkgbase)
    if merge_into:
        merge_into_uri = aur_location + '/pkgbase/' + merge_into + '/'
        body = '%s [1] filed a request to merge %s [2] into %s [3]:' % \
               (user, pkgbase, merge_into)
        body += '\n\n' + text
        refs = '[1] ' + user_uri + '\n'
        refs += '[2] ' + pkgbase_uri + '\n'
        refs += '[3] ' + merge_into_uri
    else:
        body = '%s [1] filed a %s request for %s [2]:' % \
               (user, reqtype, pkgbase)
        body += '\n\n' + text
        refs = '[1] ' + user_uri + '\n'
        refs += '[2] ' + pkgbase_uri + '\n'
    thread_id = '<pkg-request-' + reqid + '@aur.archlinux.org>'
    headers = headers_reply(thread_id)
    headers.update(headers_cc(cc))

    send_notification(to, subject, body, refs, headers)

def request_close(cur, uid, reqid, reason):
    user = username_from_id(cur, uid)
    pkgbase_id = pkgbase_from_pkgreq(cur, reqid)
    to = [aur_request_ml]
    cc = get_request_recipients(cur, pkgbase_id, uid)
    text = get_request_closure_comment(cur, reqid);

    user_uri = aur_location + '/account/' + user + '/'

    subject = '[PRQ#%d] Request %s' % (int(reqid), reason.title())
    body = 'Request #%d has been %s by %s [1]' % (int(reqid), reason, user)
    if text.strip() == '':
        body += '.'
    else:
        body += ':\n\n' + text
    refs = '[1] ' + user_uri
    thread_id = '<pkg-request-' + reqid + '@aur.archlinux.org>'
    headers = headers_reply(thread_id)
    headers.update(headers_cc(cc))

    send_notification(to, subject, body, refs, headers)


if __name__ == '__main__':
    action = sys.argv[1]
    action_map = {
        'send-resetkey': send_resetkey,
        'welcome': welcome,
        'comment': comment,
        'flag': flag,
        'comaintainer-add': comaintainer_add,
        'comaintainer-remove': comaintainer_remove,
        'delete': delete,
        'request-open': request_open,
        'request-close': request_close,
    }

    db = mysql.connector.connect(host=aur_db_host, user=aur_db_user,
                                 passwd=aur_db_pass, db=aur_db_name,
                                 unix_socket=aur_db_socket, buffered=True)
    cur = db.cursor()

    action_map[action](cur, *sys.argv[2:])

    db.commit()
    db.close()
