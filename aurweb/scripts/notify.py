#!/usr/bin/env python3

import email.mime.text
import subprocess
import sys
import textwrap

import aurweb.config
import aurweb.db

aur_location = aurweb.config.get('options', 'aur_location')


def headers_cc(cclist):
    return {'Cc': str.join(', ', cclist)}


def headers_msgid(thread_id):
    return {'Message-ID': thread_id}


def headers_reply(thread_id):
    return {'In-Reply-To': thread_id, 'References': thread_id}


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


class Notification:
    def get_refs(self):
        return ()

    def get_headers(self):
        return {}

    def send(self):
        body = ''
        for line in self.get_body().splitlines():
            body += textwrap.fill(line, break_long_words=False) + '\n'
        for i, ref in enumerate(self.get_refs()):
            body += '\n' + '[%d] %s' % (i + 1, ref)
        body = body.rstrip()

        sendmail = aurweb.config.get('notifications', 'sendmail')
        sender = aurweb.config.get('notifications', 'sender')
        reply_to = aurweb.config.get('notifications', 'reply-to')

        for recipient in self.get_recipients():
            msg = email.mime.text.MIMEText(body, 'plain', 'utf-8')
            msg['Subject'] = self.get_subject()
            msg['From'] = sender
            msg['Reply-to'] = reply_to
            msg['To'] = recipient

            for key, value in self.get_headers().items():
                msg[key] = value

            p = subprocess.Popen([sendmail, '-t', '-oi'],
                                 stdin=subprocess.PIPE)
            p.communicate(msg.as_bytes())


class ResetKeyNotification(Notification):
    def __init__(self, conn, uid):
        cur = conn.execute('SELECT UserName, Email, ResetKey FROM Users ' +
                           'WHERE ID = ?', [uid])
        self._username, self._to, self._resetkey = cur.fetchone()

    def get_recipients(self):
        return [self._to]

    def get_subject(self):
        return 'AUR Password Reset'

    def get_body(self):
        return 'A password reset request was submitted for the account %s ' \
               'associated with your email address. If you wish to reset ' \
               'your password follow the link [1] below, otherwise ignore ' \
               'this message and nothing will happen.' % (self._username)

    def get_refs(self):
        return (aur_location + '/passreset/?resetkey=' + self._resetkey,)


class WelcomeNotification(ResetKeyNotification):
    def get_subject(self):
        return 'Welcome to the Arch User Repository'

    def get_body(self):
        return 'Welcome to the Arch User Repository! In order to set an ' \
               'initial password for your new account, please click the ' \
               'link [1] below. If the link does not work, try copying and ' \
               'pasting it into your browser.'


class CommentNotification(Notification):
    def __init__(self, conn, uid, pkgbase_id, comment_id):
        self._user = username_from_id(conn, uid)
        self._pkgbase = pkgbase_from_id(conn, pkgbase_id)
        cur = conn.execute('SELECT DISTINCT Users.Email FROM Users ' +
                           'INNER JOIN PackageNotifications ' +
                           'ON PackageNotifications.UserID = Users.ID WHERE ' +
                           'Users.CommentNotify = 1 AND ' +
                           'PackageNotifications.UserID != ? AND ' +
                           'PackageNotifications.PackageBaseID = ?',
                           [uid, pkgbase_id])
        self._to = [row[0] for row in cur.fetchall()]
        cur = conn.execute('SELECT Comments FROM PackageComments WHERE ID = ?',
                           [comment_id])
        self._text = cur.fetchone()[0]

    def get_recipients(self):
        return self._to

    def get_subject(self):
        return 'AUR Comment for %s' % (self._pkgbase)

    def get_body(self):
        body = '%s [1] added the following comment to %s [2]:' % \
               (self._user, self._pkgbase)
        body += '\n\n' + self._text + '\n\n'
        body += 'If you no longer wish to receive notifications about this ' \
                'package, please go to the package page [2] and select ' \
                '"%s".' % ('Disable notifications')
        return body

    def get_refs(self):
        return (aur_location + '/account/' + self._user + '/',
                aur_location + '/pkgbase/' + self._pkgbase + '/')

    def get_headers(self):
        thread_id = '<pkg-notifications-' + self._pkgbase + \
                    '@aur.archlinux.org>'
        return headers_reply(thread_id)


class UpdateNotification(Notification):
    def __init__(self, conn, uid, pkgbase_id):
        self._user = username_from_id(conn, uid)
        self._pkgbase = pkgbase_from_id(conn, pkgbase_id)
        cur = conn.execute('SELECT DISTINCT Users.Email FROM Users ' +
                           'INNER JOIN PackageNotifications ' +
                           'ON PackageNotifications.UserID = Users.ID WHERE ' +
                           'Users.UpdateNotify = 1 AND ' +
                           'PackageNotifications.UserID != ? AND ' +
                           'PackageNotifications.PackageBaseID = ?',
                           [uid, pkgbase_id])
        self._to = [row[0] for row in cur.fetchall()]

    def get_recipients(self):
        return self._to

    def get_subject(self):
        return 'AUR Package Update: %s' % (self._pkgbase)

    def get_body(self):
        body = '%s [1] pushed a new commit to %s [2].' % \
               (self._user, self._pkgbase)
        body += '\n\n'
        body += 'If you no longer wish to receive notifications about this ' \
                'package, please go to the package page [2] and select ' \
                '"%s".' % ('Disable notifications')
        return body

    def get_refs(self):
        return (aur_location + '/account/' + self._user + '/',
                aur_location + '/pkgbase/' + self._pkgbase + '/')

    def get_headers(self):
        thread_id = '<pkg-notifications-' + self._pkgbase + \
                    '@aur.archlinux.org>'
        return headers_reply(thread_id)


class FlagNotification(Notification):
    def __init__(self, conn, uid, pkgbase_id):
        self._user = username_from_id(conn, uid)
        self._pkgbase = pkgbase_from_id(conn, pkgbase_id)
        cur = conn.execute('SELECT DISTINCT Users.Email FROM Users ' +
                           'LEFT JOIN PackageComaintainers ' +
                           'ON PackageComaintainers.UsersID = Users.ID ' +
                           'INNER JOIN PackageBases ' +
                           'ON PackageBases.MaintainerUID = Users.ID OR ' +
                           'PackageBases.ID = PackageComaintainers.PackageBaseID ' +
                           'WHERE PackageBases.ID = ?', [pkgbase_id])
        self._to = [row[0] for row in cur.fetchall()]
        cur = conn.execute('SELECT FlaggerComment FROM PackageBases WHERE ' +
                           'ID = ?', [pkgbase_id])
        self._text = cur.fetchone()[0]

    def get_recipients(self):
        return self._to

    def get_subject(self):
        return 'AUR Out-of-date Notification for %s' % (self._pkgbase)

    def get_body(self):
        body = 'Your package %s [1] has been flagged out-of-date by ' \
               '%s [2]:' % (self._pkgbase, self._user)
        body += '\n\n' + self._text
        return body

    def get_refs(self):
        return (aur_location + '/pkgbase/' + self._pkgbase + '/',
                aur_location + '/account/' + self._user + '/')


class OwnershipEventNotification(Notification):
    def __init__(self, conn, uid, pkgbase_id):
        self._user = username_from_id(conn, uid)
        self._pkgbase = pkgbase_from_id(conn, pkgbase_id)
        cur = conn.execute('SELECT DISTINCT Users.Email FROM Users ' +
                           'INNER JOIN PackageNotifications ' +
                           'ON PackageNotifications.UserID = Users.ID WHERE ' +
                           'Users.OwnershipNotify = 1 AND ' +
                           'PackageNotifications.UserID != ? AND ' +
                           'PackageNotifications.PackageBaseID = ?',
                           [uid, pkgbase_id])
        self._to = [row[0] for row in cur.fetchall()]
        cur = conn.execute('SELECT FlaggerComment FROM PackageBases WHERE ' +
                           'ID = ?', [pkgbase_id])
        self._text = cur.fetchone()[0]

    def get_recipients(self):
        return self._to

    def get_subject(self):
        return 'AUR Ownership Notification for %s' % (self._pkgbase)

    def get_refs(self):
        return (aur_location + '/pkgbase/' + self._pkgbase + '/',
                aur_location + '/account/' + self._user + '/')


class AdoptNotification(OwnershipEventNotification):
    def get_body(self):
        return 'The package %s [1] was adopted by %s [2].' % \
               (self._pkgbase, self._user)


class DisownNotification(OwnershipEventNotification):
    def get_body(self):
        return 'The package %s [1] was disowned by %s [2].' % \
               (self._pkgbase, self._user)


class ComaintainershipEventNotification(Notification):
    def __init__(self, conn, uid, pkgbase_id):
        self._pkgbase = pkgbase_from_id(conn, pkgbase_id)
        self._to = get_user_email(conn, uid)

    def get_recipients(self):
        return [self._to]

    def get_subject(self):
        return 'AUR Co-Maintainer Notification for %s' % (self._pkgbase)

    def get_refs(self):
        return (aur_location + '/pkgbase/' + self._pkgbase + '/',)


class ComaintainerAddNotification(ComaintainershipEventNotification):
    def get_body(self):
        return 'You were added to the co-maintainer list of %s [1].' % \
               (self._pkgbase)


class ComaintainerRemoveNotification(ComaintainershipEventNotification):
    def get_body(self):
        return 'You were removed from the co-maintainer list of %s [1].' % \
               (self._pkgbase)


class DeleteNotification(Notification):
    def __init__(self, conn, uid, old_pkgbase_id, new_pkgbase_id=None):
        self._user = username_from_id(conn, uid)
        self._old_pkgbase = pkgbase_from_id(conn, old_pkgbase_id)
        if new_pkgbase_id:
            self._new_pkgbase = pkgbase_from_id(conn, new_pkgbase_id)
        else:
            self._new_pkgbase = None
        cur = conn.execute('SELECT DISTINCT Users.Email FROM Users ' +
                           'INNER JOIN PackageNotifications ' +
                           'ON PackageNotifications.UserID = Users.ID WHERE ' +
                           'PackageNotifications.UserID != ? AND ' +
                           'PackageNotifications.PackageBaseID = ?',
                           [uid, old_pkgbase_id])
        self._to = [row[0] for row in cur.fetchall()]

    def get_recipients(self):
        return self._to

    def get_subject(self):
        return 'AUR Package deleted: %s' % (self._old_pkgbase)

    def get_body(self):
        if self._new_pkgbase:
            return '%s [1] merged %s [2] into %s [3].\n\n' \
                   'If you no longer wish receive notifications about the ' \
                   'new package, please go to [3] and click "%s".' % \
                   (self._user, self._old_pkgbase, self._new_pkgbase,
                    'Disable notifications')
        else:
            return '%s [1] deleted %s [2].\n\n' \
                   'You will no longer receive notifications about this ' \
                   'package.' % (self._user, self._old_pkgbase)

    def get_refs(self):
        refs = (aur_location + '/account/' + self._user + '/',
                aur_location + '/pkgbase/' + self._old_pkgbase + '/')
        if self._new_pkgbase:
            refs += (aur_location + '/pkgbase/' + self._new_pkgbase + '/',)
        return refs


class RequestOpenNotification(Notification):
    def __init__(self, conn, uid, reqid, reqtype, pkgbase_id, merge_into=None):
        self._user = username_from_id(conn, uid)
        self._pkgbase = pkgbase_from_id(conn, pkgbase_id)
        cur = conn.execute('SELECT DISTINCT Users.Email FROM PackageRequests ' +
                           'INNER JOIN PackageBases ' +
                           'ON PackageBases.ID = PackageRequests.PackageBaseID ' +
                           'INNER JOIN Users ' +
                           'ON Users.ID = PackageRequests.UsersID ' +
                           'OR Users.ID = PackageBases.MaintainerUID ' +
                           'WHERE PackageRequests.ID = ?', [reqid])
        self._to = aurweb.config.get('options', 'aur_request_ml')
        self._cc = [row[0] for row in cur.fetchall()]
        cur = conn.execute('SELECT Comments FROM PackageRequests WHERE ID = ?',
                           [reqid])
        self._text = cur.fetchone()[0]
        self._reqid = int(reqid)
        self._reqtype = reqtype
        self._merge_into = merge_into

    def get_recipients(self):
        return [self._to]

    def get_subject(self):
        return '[PRQ#%d] %s Request for %s' % \
               (self._reqid, self._reqtype.title(), self._pkgbase)

    def get_body(self):
        if self._merge_into:
            body = '%s [1] filed a request to merge %s [2] into %s [3]:' % \
                   (self._user, self._pkgbase, self._merge_into)
            body += '\n\n' + self._text
        else:
            body = '%s [1] filed a %s request for %s [2]:' % \
                   (self._user, self._reqtype, self._pkgbase)
            body += '\n\n' + self._text
        return body

    def get_refs(self):
        refs = (aur_location + '/account/' + self._user + '/',
                aur_location + '/pkgbase/' + self._pkgbase + '/')
        if self._merge_into:
            refs += (aur_location + '/pkgbase/' + self._merge_into + '/',)
        return refs

    def get_headers(self):
        thread_id = '<pkg-request-' + str(self._reqid) + '@aur.archlinux.org>'
        # Use a deterministic Message-ID for the first email referencing a
        # request.
        headers = headers_msgid(thread_id)
        headers.update(headers_cc(self._cc))
        return headers


class RequestCloseNotification(Notification):
    def __init__(self, conn, uid, reqid, reason):
        self._user = username_from_id(conn, uid) if int(uid) else None
        cur = conn.execute('SELECT DISTINCT Users.Email FROM PackageRequests ' +
                           'INNER JOIN PackageBases ' +
                           'ON PackageBases.ID = PackageRequests.PackageBaseID ' +
                           'INNER JOIN Users ' +
                           'ON Users.ID = PackageRequests.UsersID ' +
                           'OR Users.ID = PackageBases.MaintainerUID ' +
                           'WHERE PackageRequests.ID = ?', [reqid])
        self._to = aurweb.config.get('options', 'aur_request_ml')
        self._cc = [row[0] for row in cur.fetchall()]
        cur = conn.execute('SELECT ClosureComment FROM PackageRequests ' +
                           'WHERE ID = ?', [reqid])
        self._text = cur.fetchone()[0]
        self._reqid = int(reqid)
        self._reason = reason

    def get_recipients(self):
        return [self._to]

    def get_subject(self):
        return '[PRQ#%d] Request %s' % (self._reqid, self._reason.title())

    def get_body(self):
        if self._user:
            body = 'Request #%d has been %s by %s [1]' % \
                   (self._reqid, self._reason, self._user)
        else:
            body = 'Request #%d has been %s automatically by the Arch User ' \
                   'Repository package request system' % \
                   (self._reqid, self._reason)
        if self._text.strip() == '':
            body += '.'
        else:
            body += ':\n\n' + self._text
        return body

    def get_refs(self):
        if self._user:
            return (aur_location + '/account/' + self._user + '/',)
        else:
            return ()

    def get_headers(self):
        thread_id = '<pkg-request-' + str(self._reqid) + '@aur.archlinux.org>'
        headers = headers_reply(thread_id)
        headers.update(headers_cc(self._cc))
        return headers


class TUVoteReminderNotification(Notification):
    def __init__(self, conn, vote_id):
        self._vote_id = int(vote_id)
        cur = conn.execute('SELECT Email FROM Users ' +
                           'WHERE AccountTypeID IN (2, 4) AND ID NOT IN ' +
                           '(SELECT UserID FROM TU_Votes ' +
                           'WHERE TU_Votes.VoteID = ?)', [vote_id])
        self._to = [row[0] for row in cur.fetchall()]

    def get_recipients(self):
        return self._to

    def get_subject(self):
        return 'TU Vote Reminder: Proposal %d' % (self._vote_id)

    def get_body(self):
        return 'Please remember to cast your vote on proposal %d [1]. ' \
               'The voting period ends in less than 48 hours.' % \
               (self._vote_id)

    def get_refs(self):
        return (aur_location + '/tu/?id=' + str(self._vote_id),)


def main():
    action = sys.argv[1]
    action_map = {
        'send-resetkey': ResetKeyNotification,
        'welcome': WelcomeNotification,
        'comment': CommentNotification,
        'update': UpdateNotification,
        'flag': FlagNotification,
        'adopt': AdoptNotification,
        'disown': DisownNotification,
        'comaintainer-add': ComaintainerAddNotification,
        'comaintainer-remove': ComaintainerRemoveNotification,
        'delete': DeleteNotification,
        'request-open': RequestOpenNotification,
        'request-close': RequestCloseNotification,
        'tu-vote-reminder': TUVoteReminderNotification,
    }

    conn = aurweb.db.Connection()

    notification = action_map[action](conn, *sys.argv[2:])
    notification.send()

    conn.commit()
    conn.close()


if __name__ == '__main__':
    main()
