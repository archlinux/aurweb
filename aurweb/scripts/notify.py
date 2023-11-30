#!/usr/bin/env python3

import email.mime.text
import email.utils
import smtplib
import subprocess
import sys
import textwrap

from sqlalchemy import and_, or_

import aurweb.config
import aurweb.db
import aurweb.filters
import aurweb.l10n
from aurweb import aur_logging, db
from aurweb.models import PackageBase, User
from aurweb.models.package_comaintainer import PackageComaintainer
from aurweb.models.package_comment import PackageComment
from aurweb.models.package_notification import PackageNotification
from aurweb.models.package_request import PackageRequest
from aurweb.models.request_type import RequestType
from aurweb.models.vote import Vote

logger = aur_logging.get_logger(__name__)

aur_location = aurweb.config.get("options", "aur_location")


def headers_msgid(thread_id):
    return {"Message-ID": thread_id}


def headers_reply(thread_id):
    return {"In-Reply-To": thread_id, "References": thread_id}


class Notification:
    def get_refs(self):
        return ()

    def get_headers(self):
        return {}

    def get_cc(self):
        return []

    def get_bcc(self):
        return []

    def get_body_fmt(self, lang):
        body = ""
        for line in self.get_body(lang).splitlines():
            if line == "--":
                body += "--\n"
                continue
            body += textwrap.fill(line, break_long_words=False) + "\n"
        for i, ref in enumerate(self.get_refs()):
            body += "\n" + "[%d] %s" % (i + 1, ref)
        return body.rstrip()

    def _send(self) -> None:
        sendmail = aurweb.config.get("notifications", "sendmail")
        sender = aurweb.config.get("notifications", "sender")
        reply_to = aurweb.config.get("notifications", "reply-to")
        reason = self.__class__.__name__
        if reason.endswith("Notification"):
            reason = reason[: -len("Notification")]

        for recipient in self.get_recipients():
            to, lang = recipient
            msg = email.mime.text.MIMEText(self.get_body_fmt(lang), "plain", "utf-8")
            msg["Subject"] = self.get_subject(lang)
            msg["From"] = sender
            msg["Reply-to"] = reply_to
            msg["To"] = to
            if self.get_cc():
                msg["Cc"] = str.join(", ", self.get_cc())
            msg["X-AUR-Reason"] = reason
            msg["Date"] = email.utils.formatdate(localtime=True)

            for key, value in self.get_headers().items():
                msg[key] = value

            sendmail = aurweb.config.get("notifications", "sendmail")
            if sendmail:
                # send email using the sendmail binary specified in the
                # configuration file
                p = subprocess.Popen([sendmail, "-t", "-oi"], stdin=subprocess.PIPE)
                p.communicate(msg.as_bytes())
            else:
                # send email using smtplib; no local MTA required
                server_addr = aurweb.config.get("notifications", "smtp-server")
                server_port = aurweb.config.getint("notifications", "smtp-port")
                use_ssl = aurweb.config.getboolean("notifications", "smtp-use-ssl")
                use_starttls = aurweb.config.getboolean(
                    "notifications", "smtp-use-starttls"
                )
                user = aurweb.config.get("notifications", "smtp-user")
                passwd = aurweb.config.get("notifications", "smtp-password")

                classes = {
                    False: smtplib.SMTP,
                    True: smtplib.SMTP_SSL,
                }
                smtp_timeout = aurweb.config.getint("notifications", "smtp-timeout")
                server = classes[use_ssl](
                    server_addr, server_port, timeout=smtp_timeout
                )

                if use_starttls:
                    server.ehlo()
                    server.starttls()
                    server.ehlo()

                if user and passwd:
                    server.login(user, passwd)

                server.set_debuglevel(0)
                deliver_to = [to] + self.get_cc() + self.get_bcc()
                server.sendmail(sender, deliver_to, msg.as_bytes())
                server.quit()

    def send(self) -> None:
        try:
            self._send()
        except OSError as exc:
            logger.error(
                "Unable to emit notification due to an "
                "OSError (precise exception following)."
            )
            logger.error(str(exc))


class ResetKeyNotification(Notification):
    def __init__(self, uid):
        user = (
            db.query(User)
            .filter(and_(User.ID == uid, ~User.Suspended))
            .with_entities(
                User.Username,
                User.Email,
                User.BackupEmail,
                User.LangPreference,
                User.ResetKey,
            )
            .order_by(User.Username.asc())
            .first()
        )

        self._username = user.Username
        self._to = user.Email
        self._backup = user.BackupEmail
        self._lang = user.LangPreference
        self._resetkey = user.ResetKey

        super().__init__()

    def get_recipients(self):
        if self._backup:
            return [(self._to, self._lang), (self._backup, self._lang)]
        else:
            return [(self._to, self._lang)]

    def get_subject(self, lang):
        return aurweb.l10n.translator.translate("AUR Password Reset", lang)

    def get_body(self, lang):
        return aurweb.l10n.translator.translate(
            "A password reset request was submitted for the account "
            "{user} associated with your email address. If you wish to "
            "reset your password follow the link [1] below, otherwise "
            "ignore this message and nothing will happen.",
            lang,
        ).format(user=self._username)

    def get_refs(self):
        return (aur_location + "/passreset/?resetkey=" + self._resetkey,)


class WelcomeNotification(ResetKeyNotification):
    def get_subject(self, lang):
        return aurweb.l10n.translator.translate(
            "Welcome to the Arch User Repository", lang
        )

    def get_body(self, lang):
        return aurweb.l10n.translator.translate(
            "Welcome to the Arch User Repository! In order to set an "
            "initial password for your new account, please click the "
            "link [1] below. If the link does not work, try copying and "
            "pasting it into your browser.",
            lang,
        )


class CommentNotification(Notification):
    def __init__(self, uid, pkgbase_id, comment_id):
        self._user = db.query(User.Username).filter(User.ID == uid).first().Username
        self._pkgbase = (
            db.query(PackageBase.Name).filter(PackageBase.ID == pkgbase_id).first().Name
        )

        query = (
            db.query(User)
            .join(PackageNotification)
            .filter(
                and_(
                    User.CommentNotify,
                    PackageNotification.UserID != uid,
                    PackageNotification.PackageBaseID == pkgbase_id,
                    ~User.Suspended,
                )
            )
            .with_entities(User.Email, User.LangPreference)
            .distinct()
        )
        self._recipients = [(u.Email, u.LangPreference) for u in query]

        pkgcomment = (
            db.query(PackageComment.Comments)
            .filter(PackageComment.ID == comment_id)
            .first()
        )
        self._text = pkgcomment.Comments

        super().__init__()

    def get_recipients(self):
        return self._recipients

    def get_subject(self, lang):
        return aurweb.l10n.translator.translate(
            "AUR Comment for {pkgbase}", lang
        ).format(pkgbase=self._pkgbase)

    def get_body(self, lang):
        body = aurweb.l10n.translator.translate(
            "{user} [1] added the following comment to {pkgbase} [2]:", lang
        ).format(user=self._user, pkgbase=self._pkgbase)
        body += "\n\n" + self._text + "\n\n--\n"
        dnlabel = aurweb.l10n.translator.translate("Disable notifications", lang)
        body += aurweb.l10n.translator.translate(
            "If you no longer wish to receive notifications about this "
            "package, please go to the package page [2] and select "
            '"{label}".',
            lang,
        ).format(label=dnlabel)
        return body

    def get_refs(self):
        return (
            aur_location + "/account/" + self._user + "/",
            aur_location + "/pkgbase/" + self._pkgbase + "/",
        )

    def get_headers(self):
        thread_id = "<pkg-notifications-" + self._pkgbase + "@aur.archlinux.org>"
        return headers_reply(thread_id)


class UpdateNotification(Notification):
    def __init__(self, uid, pkgbase_id):
        self._user = db.query(User.Username).filter(User.ID == uid).first().Username
        self._pkgbase = (
            db.query(PackageBase.Name).filter(PackageBase.ID == pkgbase_id).first().Name
        )

        query = (
            db.query(User)
            .join(PackageNotification)
            .filter(
                and_(
                    User.UpdateNotify,
                    PackageNotification.UserID != uid,
                    PackageNotification.PackageBaseID == pkgbase_id,
                    ~User.Suspended,
                )
            )
            .with_entities(User.Email, User.LangPreference)
            .distinct()
        )
        self._recipients = [(u.Email, u.LangPreference) for u in query]

        super().__init__()

    def get_recipients(self):
        return self._recipients

    def get_subject(self, lang):
        return aurweb.l10n.translator.translate(
            "AUR Package Update: {pkgbase}", lang
        ).format(pkgbase=self._pkgbase)

    def get_body(self, lang):
        body = aurweb.l10n.translator.translate(
            "{user} [1] pushed a new commit to {pkgbase} [2].", lang
        ).format(user=self._user, pkgbase=self._pkgbase)
        body += "\n\n--\n"
        dnlabel = aurweb.l10n.translator.translate("Disable notifications", lang)
        body += aurweb.l10n.translator.translate(
            "If you no longer wish to receive notifications about this "
            "package, please go to the package page [2] and select "
            '"{label}".',
            lang,
        ).format(label=dnlabel)
        return body

    def get_refs(self):
        return (
            aur_location + "/account/" + self._user + "/",
            aur_location + "/pkgbase/" + self._pkgbase + "/",
        )

    def get_headers(self):
        thread_id = "<pkg-notifications-" + self._pkgbase + "@aur.archlinux.org>"
        return headers_reply(thread_id)


class FlagNotification(Notification):
    def __init__(self, uid, pkgbase_id):
        self._user = db.query(User.Username).filter(User.ID == uid).first().Username
        self._pkgbase = (
            db.query(PackageBase.Name).filter(PackageBase.ID == pkgbase_id).first().Name
        )

        query = (
            db.query(User)
            .join(PackageComaintainer, isouter=True)
            .join(
                PackageBase,
                or_(
                    PackageBase.MaintainerUID == User.ID,
                    PackageBase.ID == PackageComaintainer.PackageBaseID,
                ),
            )
            .filter(and_(PackageBase.ID == pkgbase_id, ~User.Suspended))
            .with_entities(User.Email, User.LangPreference)
            .distinct()
            .order_by(User.Email)
        )
        self._recipients = [(u.Email, u.LangPreference) for u in query]

        pkgbase = (
            db.query(PackageBase.FlaggerComment)
            .filter(PackageBase.ID == pkgbase_id)
            .first()
        )
        self._text = pkgbase.FlaggerComment

        super().__init__()

    def get_recipients(self):
        return self._recipients

    def get_subject(self, lang):
        return aurweb.l10n.translator.translate(
            "AUR Out-of-date Notification for {pkgbase}", lang
        ).format(pkgbase=self._pkgbase)

    def get_body(self, lang):
        body = aurweb.l10n.translator.translate(
            "Your package {pkgbase} [1] has been flagged out-of-date by " "{user} [2]:",
            lang,
        ).format(pkgbase=self._pkgbase, user=self._user)
        body += "\n\n" + self._text
        return body

    def get_refs(self):
        return (
            aur_location + "/pkgbase/" + self._pkgbase + "/",
            aur_location + "/account/" + self._user + "/",
        )


class OwnershipEventNotification(Notification):
    def __init__(self, uid, pkgbase_id):
        self._user = db.query(User.Username).filter(User.ID == uid).first().Username
        self._pkgbase = (
            db.query(PackageBase.Name).filter(PackageBase.ID == pkgbase_id).first().Name
        )

        query = (
            db.query(User)
            .join(PackageNotification)
            .filter(
                and_(
                    User.OwnershipNotify,
                    PackageNotification.UserID != uid,
                    PackageNotification.PackageBaseID == pkgbase_id,
                    ~User.Suspended,
                )
            )
            .with_entities(User.Email, User.LangPreference)
            .distinct()
        )
        self._recipients = [(u.Email, u.LangPreference) for u in query]

        pkgbase = (
            db.query(PackageBase.FlaggerComment)
            .filter(PackageBase.ID == pkgbase_id)
            .first()
        )
        self._text = pkgbase.FlaggerComment

        super().__init__()

    def get_recipients(self):
        return self._recipients

    def get_subject(self, lang):
        return aurweb.l10n.translator.translate(
            "AUR Ownership Notification for {pkgbase}", lang
        ).format(pkgbase=self._pkgbase)

    def get_refs(self):
        return (
            aur_location + "/pkgbase/" + self._pkgbase + "/",
            aur_location + "/account/" + self._user + "/",
        )


class AdoptNotification(OwnershipEventNotification):
    def get_body(self, lang):
        return aurweb.l10n.translator.translate(
            "The package {pkgbase} [1] was adopted by {user} [2].", lang
        ).format(pkgbase=self._pkgbase, user=self._user)


class DisownNotification(OwnershipEventNotification):
    def get_body(self, lang):
        return aurweb.l10n.translator.translate(
            "The package {pkgbase} [1] was disowned by {user} " "[2].", lang
        ).format(pkgbase=self._pkgbase, user=self._user)


class ComaintainershipEventNotification(Notification):
    def __init__(self, uid, pkgbase_id):
        self._pkgbase = (
            db.query(PackageBase.Name).filter(PackageBase.ID == pkgbase_id).first().Name
        )

        user = (
            db.query(User)
            .filter(User.ID == uid)
            .with_entities(User.Email, User.LangPreference)
            .first()
        )

        self._to = user.Email
        self._lang = user.LangPreference

        super().__init__()

    def get_recipients(self):
        return [(self._to, self._lang)]

    def get_subject(self, lang):
        return aurweb.l10n.translator.translate(
            "AUR Co-Maintainer Notification for {pkgbase}", lang
        ).format(pkgbase=self._pkgbase)

    def get_refs(self):
        return (aur_location + "/pkgbase/" + self._pkgbase + "/",)


class ComaintainerAddNotification(ComaintainershipEventNotification):
    def get_body(self, lang):
        return aurweb.l10n.translator.translate(
            "You were added to the co-maintainer list of {pkgbase} [1].", lang
        ).format(pkgbase=self._pkgbase)


class ComaintainerRemoveNotification(ComaintainershipEventNotification):
    def get_body(self, lang):
        return aurweb.l10n.translator.translate(
            "You were removed from the co-maintainer list of {pkgbase} " "[1].", lang
        ).format(pkgbase=self._pkgbase)


class DeleteNotification(Notification):
    def __init__(self, uid, old_pkgbase_id, new_pkgbase_id=None):
        self._user = db.query(User.Username).filter(User.ID == uid).first().Username
        self._old_pkgbase = (
            db.query(PackageBase.Name)
            .filter(PackageBase.ID == old_pkgbase_id)
            .first()
            .Name
        )

        self._new_pkgbase = None
        if new_pkgbase_id:
            self._new_pkgbase = (
                db.query(PackageBase.Name)
                .filter(PackageBase.ID == new_pkgbase_id)
                .first()
                .Name
            )

        query = (
            db.query(User)
            .join(PackageNotification)
            .filter(
                and_(
                    PackageNotification.UserID != uid,
                    PackageNotification.PackageBaseID == old_pkgbase_id,
                    ~User.Suspended,
                )
            )
            .with_entities(User.Email, User.LangPreference)
            .distinct()
        )
        self._recipients = [(u.Email, u.LangPreference) for u in query]

        super().__init__()

    def get_recipients(self):
        return self._recipients

    def get_subject(self, lang):
        return aurweb.l10n.translator.translate(
            "AUR Package deleted: {pkgbase}", lang
        ).format(pkgbase=self._old_pkgbase)

    def get_body(self, lang):
        if self._new_pkgbase:
            dnlabel = aurweb.l10n.translator.translate("Disable notifications", lang)
            return aurweb.l10n.translator.translate(
                "{user} [1] merged {old} [2] into {new} [3].\n\n"
                "--\n"
                "If you no longer wish receive notifications about the "
                'new package, please go to [3] and click "{label}".',
                lang,
            ).format(
                user=self._user,
                old=self._old_pkgbase,
                new=self._new_pkgbase,
                label=dnlabel,
            )
        else:
            return aurweb.l10n.translator.translate(
                "{user} [1] deleted {pkgbase} [2].\n\n"
                "You will no longer receive notifications about this "
                "package.",
                lang,
            ).format(user=self._user, pkgbase=self._old_pkgbase)

    def get_refs(self):
        refs = (
            aur_location + "/account/" + self._user + "/",
            aur_location + "/pkgbase/" + self._old_pkgbase + "/",
        )
        if self._new_pkgbase:
            refs += (aur_location + "/pkgbase/" + self._new_pkgbase + "/",)
        return refs


class RequestOpenNotification(Notification):
    def __init__(self, uid, reqid, reqtype, pkgbase_id, merge_into=None):
        self._user = db.query(User.Username).filter(User.ID == uid).first().Username
        self._pkgbase = (
            db.query(PackageBase.Name).filter(PackageBase.ID == pkgbase_id).first().Name
        )

        self._to = aurweb.config.get("options", "aur_request_ml")

        query = (
            db.query(PackageRequest)
            .join(PackageBase)
            .join(
                PackageComaintainer,
                PackageComaintainer.PackageBaseID == PackageRequest.PackageBaseID,
                isouter=True,
            )
            .join(
                User,
                or_(
                    User.ID == PackageRequest.UsersID,
                    User.ID == PackageBase.MaintainerUID,
                    User.ID == PackageComaintainer.UsersID,
                ),
            )
            .filter(and_(PackageRequest.ID == reqid, ~User.Suspended))
            .with_entities(User.Email, User.HideEmail)
            .distinct()
        )
        self._cc = [u.Email for u in query if not u.HideEmail]
        self._bcc = [u.Email for u in query if u.HideEmail]

        pkgreq = (
            db.query(PackageRequest.Comments).filter(PackageRequest.ID == reqid).first()
        )

        self._text = pkgreq.Comments
        self._reqid = int(reqid)
        self._reqtype = reqtype
        self._merge_into = merge_into

    def get_recipients(self):
        return [(self._to, "en")]

    def get_cc(self):
        return self._cc

    def get_bcc(self):
        return self._bcc

    def get_subject(self, lang):
        return "[PRQ#%d] %s Request for %s" % (
            self._reqid,
            self._reqtype.title(),
            self._pkgbase,
        )

    def get_body(self, lang):
        if self._merge_into:
            body = "%s [1] filed a request to merge %s [2] into %s [3]:" % (
                self._user,
                self._pkgbase,
                self._merge_into,
            )
            body += "\n\n" + self._text
        else:
            an = "an" if self._reqtype[0] in "aeiou" else "a"
            body = "%s [1] filed %s %s request for %s [2]:" % (
                self._user,
                an,
                self._reqtype,
                self._pkgbase,
            )
            body += "\n\n" + self._text
        return body

    def get_refs(self):
        refs = (
            aur_location + "/account/" + self._user + "/",
            aur_location + "/pkgbase/" + self._pkgbase + "/",
        )
        if self._merge_into:
            refs += (aur_location + "/pkgbase/" + self._merge_into + "/",)
        return refs

    def get_headers(self):
        thread_id = "<pkg-request-" + str(self._reqid) + "@aur.archlinux.org>"
        # Use a deterministic Message-ID for the first email referencing a
        # request.
        headers = headers_msgid(thread_id)
        return headers


class RequestCloseNotification(Notification):
    def __init__(self, uid, reqid, reason):
        user = db.query(User.Username).filter(User.ID == uid).first()
        self._user = user.Username if user else None

        self._to = aurweb.config.get("options", "aur_request_ml")

        query = (
            db.query(PackageRequest)
            .join(PackageBase)
            .join(
                PackageComaintainer,
                PackageComaintainer.PackageBaseID == PackageRequest.PackageBaseID,
                isouter=True,
            )
            .join(
                User,
                or_(
                    User.ID == PackageRequest.UsersID,
                    User.ID == PackageBase.MaintainerUID,
                    User.ID == PackageComaintainer.UsersID,
                ),
            )
            .filter(and_(PackageRequest.ID == reqid, ~User.Suspended))
            .with_entities(User.Email, User.HideEmail)
            .distinct()
        )
        self._cc = [u.Email for u in query if not u.HideEmail]
        self._bcc = [u.Email for u in query if u.HideEmail]

        pkgreq = (
            db.query(PackageRequest)
            .join(RequestType)
            .filter(PackageRequest.ID == reqid)
            .with_entities(
                PackageRequest.ClosureComment,
                RequestType.Name,
                PackageRequest.PackageBaseName,
            )
            .first()
        )

        self._text = pkgreq.ClosureComment
        self._reqtype = pkgreq.Name
        self._pkgbase = pkgreq.PackageBaseName

        self._reqid = int(reqid)
        self._reason = reason

    def get_recipients(self):
        return [(self._to, "en")]

    def get_cc(self):
        return self._cc

    def get_bcc(self):
        return self._bcc

    def get_subject(self, lang):
        return "[PRQ#%d] %s Request for %s %s" % (
            self._reqid,
            self._reqtype.title(),
            self._pkgbase,
            self._reason.title(),
        )

    def get_body(self, lang):
        if self._user:
            body = "Request #%d has been %s by %s [1]" % (
                self._reqid,
                self._reason,
                self._user,
            )
        else:
            body = (
                "Request #%d has been %s automatically by the Arch User "
                "Repository package request system" % (self._reqid, self._reason)
            )
        if self._text.strip() == "":
            body += "."
        else:
            body += ":\n\n" + self._text
        return body

    def get_refs(self):
        if self._user:
            return (aur_location + "/account/" + self._user + "/",)
        else:
            return ()

    def get_headers(self):
        thread_id = "<pkg-request-" + str(self._reqid) + "@aur.archlinux.org>"
        headers = headers_reply(thread_id)
        return headers


class VoteReminderNotification(Notification):
    def __init__(self, vote_id):
        self._vote_id = int(vote_id)

        subquery = db.query(Vote.UserID).filter(Vote.VoteID == vote_id)
        query = (
            db.query(User)
            .filter(
                and_(
                    User.AccountTypeID.in_((2, 4)),
                    ~User.ID.in_(subquery),
                    ~User.Suspended,
                )
            )
            .with_entities(User.Email, User.LangPreference)
        )
        self._recipients = [(u.Email, u.LangPreference) for u in query]

        super().__init__()

    def get_recipients(self):
        return self._recipients

    def get_subject(self, lang):
        return aurweb.l10n.translator.translate(
            "Package Maintainer Vote Reminder: Proposal {id}", lang
        ).format(id=self._vote_id)

    def get_body(self, lang):
        return aurweb.l10n.translator.translate(
            "Please remember to cast your vote on proposal {id} [1]. "
            "The voting period ends in less than 48 hours.",
            lang,
        ).format(id=self._vote_id)

    def get_refs(self):
        return (aur_location + "/package-maintainer/?id=" + str(self._vote_id),)


def main():
    db.get_engine()
    action = sys.argv[1]
    action_map = {
        "send-resetkey": ResetKeyNotification,
        "welcome": WelcomeNotification,
        "comment": CommentNotification,
        "update": UpdateNotification,
        "flag": FlagNotification,
        "adopt": AdoptNotification,
        "disown": DisownNotification,
        "comaintainer-add": ComaintainerAddNotification,
        "comaintainer-remove": ComaintainerRemoveNotification,
        "delete": DeleteNotification,
        "request-open": RequestOpenNotification,
        "request-close": RequestCloseNotification,
        "vote-reminder": VoteReminderNotification,
    }

    with db.begin():
        notification = action_map[action](*sys.argv[2:])
    notification.send()


if __name__ == "__main__":
    main()
