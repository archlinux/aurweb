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


def send_notification(to, subject, body, cc=None, reference=None):
    body = str.join('\n', [textwrap.fill(line) for line in body.splitlines()])

    for recipient in to:
        msg = email.mime.text.MIMEText(body, 'plain', 'utf-8')
        msg['Subject'] = subject
        msg['From'] = sender
        msg['Reply-to'] = reply_to
        msg['To'] = recipient

        if cc:
            msg['Cc'] = str.join(', ', cc)

        if reference:
            msg['In-Reply-To'] = reference
            msg['References'] = reference

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

def send_resetkey(cur, uid):
    cur.execute('SELECT UserName, Email, ResetKey FROM Users WHERE ID = %s',
                [uid])
    username, to, resetkey = cur.fetchone()

    subject = 'AUR Password Reset'
    body = 'A password reset request was submitted for the account %s ' \
           'associated with your email address. If you wish to reset your ' \
           'password follow the link [1] below, otherwise ignore this ' \
           'message and nothing will happen.' % (username)
    body += '\n\n'
    body += '[1] ' + aur_location + '/passreset/?resetkey=' + resetkey

    send_notification([to], subject, body)

def welcome(cur, uid):
    cur.execute('SELECT UserName, Email, ResetKey FROM Users WHERE ID = %s',
                [uid])
    username, to, resetkey = cur.fetchone()

    subject = 'Welcome to the Arch User Repository'
    body = 'Welcome to the Arch User Repository! In order to set an initial ' \
           'password for your new account, please click the link [1] below. ' \
           'If the link does not work, try copying and pasting it into your ' \
           'browser.'
    body += '\n\n'
    body += '[1] ' + aur_location + '/passreset/?resetkey=' + resetkey

    send_notification([to], subject, body)

def comment(cur, uid, pkgbase_id):
    user = username_from_id(cur, uid)
    pkgbase = pkgbase_from_id(cur, pkgbase_id)
    to = get_recipients(cur, pkgbase_id, uid)
    text = sys.stdin.read()

    uri = aur_location + '/pkgbase/' + pkgbase + '/'

    user_uri = aur_location + '/account/' + user + '/'
    pkgbase_uri = aur_location + '/pkgbase/' + pkgbase + '/'

    subject = 'AUR Comment for %s' % (pkgbase)
    body = '%s [1] added the following comment to %s [2]:' % (user, pkgbase)
    body += '\n\n' + text + '\n\n'
    body += 'If you no longer wish to receive notifications about this ' \
            'package, please go to the package page [2] and select "%s".' % \
            ('Disable notifications')
    body += '\n\n'
    body += '[1] ' + user_uri + '\n'
    body += '[2] ' + pkgbase_uri
    thread_id = '<pkg-notifications-' + pkgbase + '@aur.archlinux.org>'

    send_notification(to, subject, body, reference=thread_id)

def flag(cur, uid, pkgbase_id):
    user = username_from_id(cur, uid)
    pkgbase = pkgbase_from_id(cur, pkgbase_id)
    to = [get_maintainer_email(cur, pkgbase_id)]

    user_uri = aur_location + '/account/' + user + '/'
    pkgbase_uri = aur_location + '/pkgbase/' + pkgbase + '/'

    subject = 'AUR Out-of-date Notification for %s' % (pkgbase)
    body = 'Your package %s [1] has been flagged out-of-date by %s [2]. ' % \
           (pkgbase, user)
    body += '\n\n'
    body += '[1] ' + pkgbase_uri + '\n'
    body += '[2] ' + user_uri

    send_notification(to, subject, body)

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
               'You will no longer receive notifications about this ' \
               'package, please go to [3] and click "%s" if you wish to ' \
               'receive them again.' % \
               (user, old_pkgbase, new_pkgbase, 'Notify of new comments')
        body += '\n\n'
        body += '[1] ' + user_uri + '\n'
        body += '[2] ' + pkgbase_uri + '\n'
        body += '[3] ' + new_pkgbase_uri
    else:
        body = '%s [1] deleted %s [2].\n\n' \
               'You will no longer receive notifications about this ' \
               'package.' % (user, old_pkgbase)
        body += '\n\n'
        body += '[1] ' + user_uri + '\n'
        body += '[2] ' + pkgbase_uri

    send_notification(to, subject, body)

def request_open(cur, uid, reqid, reqtype, pkgbase_id, merge_into=None):
    user = username_from_id(cur, uid)
    pkgbase = pkgbase_from_id(cur, pkgbase_id)
    to = [aur_request_ml]
    cc = get_request_recipients(cur, pkgbase_id, uid)
    text = sys.stdin.read()

    user_uri = aur_location + '/account/' + user + '/'
    pkgbase_uri = aur_location + '/pkgbase/' + pkgbase + '/'

    subject = '[PRQ#%d] %s Request for %s' % \
              (int(reqid), reqtype.title(), pkgbase)
    if merge_into:
        merge_into_uri = aur_location + '/pkgbase/' + merge_into + '/'
        body = '%s [1] filed a request to merge %s [2] into %s [3]:' % \
               (user, pkgbase, merge_into)
        body += '\n\n' + text + '\n\n'
        body += '[1] ' + user_uri + '\n'
        body += '[2] ' + pkgbase_uri + '\n'
        body += '[3] ' + merge_into_uri
    else:
        body = '%s [1] filed a %s request for %s [2]:' % \
               (user, reqtype, pkgbase)
        body += '\n\n' + text + '\n\n'
        body += '[1] ' + user_uri + '\n'
        body += '[2] ' + pkgbase_uri + '\n'
    thread_id = '<pkg-request-' + reqid + '@aur.archlinux.org>'

    send_notification(to, subject, body, cc, thread_id)

def request_close(cur, uid, reqid, reason):
    user = username_from_id(cur, uid)
    pkgbase_id = pkgbase_from_pkgreq(cur, reqid)
    to = [aur_request_ml]
    cc = get_request_recipients(cur, pkgbase_id, uid)
    text = sys.stdin.read()

    user_uri = aur_location + '/account/' + user + '/'

    subject = '[PRQ#%d] Request %s' % (int(reqid), reason.title())
    body = 'Request #%d has been %s by %s [1]' % (int(reqid), reason, user)
    if text.strip() == '':
        body += '.\n\n'
    else:
        body += ':\n\n' + text + '\n\n'
    body += '[1] ' + user_uri
    thread_id = '<pkg-request-' + reqid + '@aur.archlinux.org>'

    send_notification(to, subject, body, cc, thread_id)


if __name__ == '__main__':
    action = sys.argv[1]
    action_map = {
        'send-resetkey': send_resetkey,
        'welcome': welcome,
        'comment': comment,
        'flag': flag,
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
