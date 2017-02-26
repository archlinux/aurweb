#!/usr/bin/python3

import email.mime.text
import subprocess
import sys
import textwrap

import aurweb.config
import aurweb.db

aur_location = aurweb.config.get('options', 'aur_location')
aur_request_ml = aurweb.config.get('options', 'aur_request_ml')

sendmail = aurweb.config.get('notifications', 'sendmail')
sender = aurweb.config.get('notifications', 'sender')
reply_to = aurweb.config.get('notifications', 'reply-to')


def headers_cc(cclist):
    return {'Cc': str.join(', ', cclist)}


def headers_msgid(thread_id):
    return {'Message-ID': thread_id}


def headers_reply(thread_id):
    return {'In-Reply-To': thread_id, 'References': thread_id}


def send_notification(to, subject, body, refs, headers={}):
    wrapped = ''
    for line in body.splitlines():
        wrapped += textwrap.fill(line, break_long_words=False) + '\n'
    if refs:
        body = wrapped + '\n' + refs
    else:
        body = wrapped

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


def username_from_id(conn, uid):
    cur = conn.execute('SELECT UserName FROM Users WHERE ID = ?', [uid])
    return cur.fetchone()[0]


def pkgbase_from_id(conn, pkgbase_id):
    cur = conn.execute('SELECT Name FROM PackageBases WHERE ID = ?',
                       [pkgbase_id])
    return cur.fetchone()[0]


def pkgbase_from_pkgreq(conn, reqid):
    cur = conn.execute('SELECT PackageBaseID FROM PackageRequests ' +
                       'WHERE ID = ?', [reqid])
    return cur.fetchone()[0]


def get_user_email(conn, uid):
    cur = conn.execute('SELECT Email FROM Users WHERE ID = ?', [uid])
    return cur.fetchone()[0]


def get_flag_recipients(conn, pkgbase_id):
    cur = conn.execute('SELECT DISTINCT Users.Email FROM Users ' +
                       'LEFT JOIN PackageComaintainers ' +
                       'ON PackageComaintainers.UsersID = Users.ID ' +
                       'INNER JOIN PackageBases ' +
                       'ON PackageBases.MaintainerUID = Users.ID OR ' +
                       'PackageBases.ID = PackageComaintainers.PackageBaseID ' +
                       'WHERE PackageBases.ID = ?', [pkgbase_id])
    return [row[0] for row in cur.fetchall()]


def get_recipients(conn, pkgbase_id, uid):
    cur = conn.execute('SELECT DISTINCT Users.Email FROM Users ' +
                       'INNER JOIN PackageNotifications ' +
                       'ON PackageNotifications.UserID = Users.ID WHERE ' +
                       'PackageNotifications.UserID != ? AND ' +
                       'PackageNotifications.PackageBaseID = ?',
                       [uid, pkgbase_id])
    return [row[0] for row in cur.fetchall()]


def get_comment_recipients(conn, pkgbase_id, uid):
    cur = conn.execute('SELECT DISTINCT Users.Email FROM Users ' +
                       'INNER JOIN PackageNotifications ' +
                       'ON PackageNotifications.UserID = Users.ID WHERE ' +
                       'Users.CommentNotify = 1 AND ' +
                       'PackageNotifications.UserID != ? AND ' +
                       'PackageNotifications.PackageBaseID = ?',
                       [uid, pkgbase_id])
    return [row[0] for row in cur.fetchall()]


def get_update_recipients(conn, pkgbase_id, uid):
    cur = conn.execute('SELECT DISTINCT Users.Email FROM Users ' +
                       'INNER JOIN PackageNotifications ' +
                       'ON PackageNotifications.UserID = Users.ID WHERE ' +
                       'Users.UpdateNotify = 1 AND ' +
                       'PackageNotifications.UserID != ? AND ' +
                       'PackageNotifications.PackageBaseID = ?',
                       [uid, pkgbase_id])
    return [row[0] for row in cur.fetchall()]


def get_ownership_recipients(conn, pkgbase_id, uid):
    cur = conn.execute('SELECT DISTINCT Users.Email FROM Users ' +
                       'INNER JOIN PackageNotifications ' +
                       'ON PackageNotifications.UserID = Users.ID WHERE ' +
                       'Users.OwnershipNotify = 1 AND ' +
                       'PackageNotifications.UserID != ? AND ' +
                       'PackageNotifications.PackageBaseID = ?',
                       [uid, pkgbase_id])
    return [row[0] for row in cur.fetchall()]


def get_request_recipients(conn, reqid):
    cur = conn.execute('SELECT DISTINCT Users.Email FROM PackageRequests ' +
                       'INNER JOIN PackageBases ' +
                       'ON PackageBases.ID = PackageRequests.PackageBaseID ' +
                       'INNER JOIN Users ' +
                       'ON Users.ID = PackageRequests.UsersID ' +
                       'OR Users.ID = PackageBases.MaintainerUID ' +
                       'WHERE PackageRequests.ID = ?', [reqid])
    return [row[0] for row in cur.fetchall()]


def get_tu_vote_reminder_recipients(conn, vote_id):
    cur = conn.execute('SELECT Email FROM Users ' +
                       'WHERE AccountTypeID = 2 AND ID NOT IN ' +
                       '(SELECT UserID FROM TU_Votes ' +
                       'WHERE TU_Votes.VoteID = ?)', [vote_id])
    return [row[0] for row in cur.fetchall()]


def get_comment(conn, comment_id):
    cur = conn.execute('SELECT Comments FROM PackageComments WHERE ID = ?',
                       [comment_id])
    return cur.fetchone()[0]


def get_flagger_comment(conn, pkgbase_id):
    cur = conn.execute('SELECT FlaggerComment FROM PackageBases WHERE ID = ?',
                       [pkgbase_id])
    return cur.fetchone()[0]


def get_request_comment(conn, reqid):
    cur = conn.execute('SELECT Comments FROM PackageRequests WHERE ID = ?',
                       [reqid])
    return cur.fetchone()[0]


def get_request_closure_comment(conn, reqid):
    cur = conn.execute('SELECT ClosureComment FROM PackageRequests ' +
                       'WHERE ID = ?', [reqid])
    return cur.fetchone()[0]


def send_resetkey(conn, uid):
    cur = conn.execute('SELECT UserName, Email, ResetKey FROM Users ' +
                       'WHERE ID = ?', [uid])
    username, to, resetkey = cur.fetchone()

    subject = 'AUR Password Reset'
    body = 'A password reset request was submitted for the account %s ' \
           'associated with your email address. If you wish to reset your ' \
           'password follow the link [1] below, otherwise ignore this ' \
           'message and nothing will happen.' % (username)
    refs = '[1] ' + aur_location + '/passreset/?resetkey=' + resetkey

    send_notification([to], subject, body, refs)


def welcome(conn, uid):
    cur = conn.execute('SELECT UserName, Email, ResetKey FROM Users ' +
                       'WHERE ID = ?', [uid])
    username, to, resetkey = cur.fetchone()

    subject = 'Welcome to the Arch User Repository'
    body = 'Welcome to the Arch User Repository! In order to set an initial ' \
           'password for your new account, please click the link [1] below. ' \
           'If the link does not work, try copying and pasting it into your ' \
           'browser.'
    refs = '[1] ' + aur_location + '/passreset/?resetkey=' + resetkey

    send_notification([to], subject, body, refs)


def comment(conn, uid, pkgbase_id, comment_id):
    user = username_from_id(conn, uid)
    pkgbase = pkgbase_from_id(conn, pkgbase_id)
    to = get_comment_recipients(conn, pkgbase_id, uid)
    text = get_comment(conn, comment_id)

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


def update(conn, uid, pkgbase_id):
    user = username_from_id(conn, uid)
    pkgbase = pkgbase_from_id(conn, pkgbase_id)
    to = get_update_recipients(conn, pkgbase_id, uid)

    user_uri = aur_location + '/account/' + user + '/'
    pkgbase_uri = aur_location + '/pkgbase/' + pkgbase + '/'

    subject = 'AUR Package Update: %s' % (pkgbase)
    body = '%s [1] pushed a new commit to %s [2].' % (user, pkgbase)
    body += '\n\n'
    body += 'If you no longer wish to receive notifications about this ' \
            'package, please go to the package page [2] and select "%s".' % \
            ('Disable notifications')
    refs = '[1] ' + user_uri + '\n'
    refs += '[2] ' + pkgbase_uri
    thread_id = '<pkg-notifications-' + pkgbase + '@aur.archlinux.org>'
    headers = headers_reply(thread_id)

    send_notification(to, subject, body, refs, headers)


def flag(conn, uid, pkgbase_id):
    user = username_from_id(conn, uid)
    pkgbase = pkgbase_from_id(conn, pkgbase_id)
    to = get_flag_recipients(conn, pkgbase_id)
    text = get_flagger_comment(conn, pkgbase_id)

    user_uri = aur_location + '/account/' + user + '/'
    pkgbase_uri = aur_location + '/pkgbase/' + pkgbase + '/'

    subject = 'AUR Out-of-date Notification for %s' % (pkgbase)
    body = 'Your package %s [1] has been flagged out-of-date by %s [2]:' % \
           (pkgbase, user)
    body += '\n\n' + text
    refs = '[1] ' + pkgbase_uri + '\n'
    refs += '[2] ' + user_uri

    send_notification(to, subject, body, refs)


def adopt(conn, pkgbase_id, uid):
    user = username_from_id(conn, uid)
    pkgbase = pkgbase_from_id(conn, pkgbase_id)
    to = get_ownership_recipients(conn, pkgbase_id, uid)

    user_uri = aur_location + '/account/' + user + '/'
    pkgbase_uri = aur_location + '/pkgbase/' + pkgbase + '/'

    subject = 'AUR Ownership Notification for %s' % (pkgbase)
    body = 'The package %s [1] was adopted by %s [2].' % (pkgbase, user)
    refs = '[1] ' + pkgbase_uri + '\n'
    refs += '[2] ' + user_uri

    send_notification(to, subject, body, refs)


def disown(conn, pkgbase_id, uid):
    user = username_from_id(conn, uid)
    pkgbase = pkgbase_from_id(conn, pkgbase_id)
    to = get_ownership_recipients(conn, pkgbase_id, uid)

    user_uri = aur_location + '/account/' + user + '/'
    pkgbase_uri = aur_location + '/pkgbase/' + pkgbase + '/'

    subject = 'AUR Ownership Notification for %s' % (pkgbase)
    body = 'The package %s [1] was disowned by %s [2].' % (pkgbase, user)
    refs = '[1] ' + pkgbase_uri + '\n'
    refs += '[2] ' + user_uri

    send_notification(to, subject, body, refs)


def comaintainer_add(conn, pkgbase_id, uid):
    pkgbase = pkgbase_from_id(conn, pkgbase_id)
    to = [get_user_email(conn, uid)]

    pkgbase_uri = aur_location + '/pkgbase/' + pkgbase + '/'

    subject = 'AUR Co-Maintainer Notification for %s' % (pkgbase)
    body = 'You were added to the co-maintainer list of %s [1].' % (pkgbase)
    refs = '[1] ' + pkgbase_uri + '\n'

    send_notification(to, subject, body, refs)


def comaintainer_remove(conn, pkgbase_id, uid):
    pkgbase = pkgbase_from_id(conn, pkgbase_id)
    to = [get_user_email(conn, uid)]

    pkgbase_uri = aur_location + '/pkgbase/' + pkgbase + '/'

    subject = 'AUR Co-Maintainer Notification for %s' % (pkgbase)
    body = ('You were removed from the co-maintainer list of %s [1].' %
            (pkgbase))
    refs = '[1] ' + pkgbase_uri + '\n'

    send_notification(to, subject, body, refs)


def delete(conn, uid, old_pkgbase_id, new_pkgbase_id=None):
    user = username_from_id(conn, uid)
    old_pkgbase = pkgbase_from_id(conn, old_pkgbase_id)
    if new_pkgbase_id:
        new_pkgbase = pkgbase_from_id(conn, new_pkgbase_id)
    to = get_recipients(conn, old_pkgbase_id, uid)

    user_uri = aur_location + '/account/' + user + '/'
    pkgbase_uri = aur_location + '/pkgbase/' + old_pkgbase + '/'

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


def request_open(conn, uid, reqid, reqtype, pkgbase_id, merge_into=None):
    user = username_from_id(conn, uid)
    pkgbase = pkgbase_from_id(conn, pkgbase_id)
    to = [aur_request_ml]
    cc = get_request_recipients(conn, reqid)
    text = get_request_comment(conn, reqid)

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
    # Use a deterministic Message-ID for the first email referencing a request.
    headers = headers_msgid(thread_id)
    headers.update(headers_cc(cc))

    send_notification(to, subject, body, refs, headers)


def request_close(conn, uid, reqid, reason):
    to = [aur_request_ml]
    cc = get_request_recipients(conn, reqid)
    text = get_request_closure_comment(conn, reqid)

    subject = '[PRQ#%d] Request %s' % (int(reqid), reason.title())
    if int(uid):
        user = username_from_id(conn, uid)
        user_uri = aur_location + '/account/' + user + '/'
        body = 'Request #%d has been %s by %s [1]' % (int(reqid), reason, user)
        refs = '[1] ' + user_uri
    else:
        body = 'Request #%d has been %s automatically by the Arch User ' \
               'Repository package request system' % (int(reqid), reason)
        refs = None
    if text.strip() == '':
        body += '.'
    else:
        body += ':\n\n' + text
    thread_id = '<pkg-request-' + reqid + '@aur.archlinux.org>'
    headers = headers_reply(thread_id)
    headers.update(headers_cc(cc))

    send_notification(to, subject, body, refs, headers)


def tu_vote_reminder(conn, vote_id):
    to = get_tu_vote_reminder_recipients(conn, vote_id)

    vote_uri = aur_location + '/tu/?id=' + vote_id

    subject = 'TU Vote Reminder: Proposal %d' % (int(vote_id))
    body = 'Please remember to cast your vote on proposal %d [1]. ' \
           'The voting period ends in less than 48 hours.' % (int(vote_id))
    refs = '[1] ' + vote_uri

    send_notification(to, subject, body, refs)


def main():
    action = sys.argv[1]
    action_map = {
        'send-resetkey': send_resetkey,
        'welcome': welcome,
        'comment': comment,
        'update': update,
        'flag': flag,
        'adopt': adopt,
        'disown': disown,
        'comaintainer-add': comaintainer_add,
        'comaintainer-remove': comaintainer_remove,
        'delete': delete,
        'request-open': request_open,
        'request-close': request_close,
        'tu-vote-reminder': tu_vote_reminder,
    }

    conn = aurweb.db.Connection()

    action_map[action](conn, *sys.argv[2:])

    conn.commit()
    conn.close()


if __name__ == '__main__':
    main()
