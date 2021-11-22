""" Fake SMTP clients that can be used for testing. """


class FakeSMTP:
    """ A fake version of smtplib.SMTP used for testing. """

    starttls_enabled = False
    use_ssl = False

    def __init__(self):
        self.emails = []
        self.count = 0
        self.ehlo_count = 0
        self.quit_count = 0
        self.set_debuglevel_count = 0
        self.user = None
        self.passwd = None

    def ehlo(self) -> None:
        self.ehlo_count += 1

    def starttls(self) -> None:
        self.starttls_enabled = True

    def set_debuglevel(self, level: int = 0) -> None:
        self.set_debuglevel_count += 1

    def login(self, user: str, passwd: str) -> None:
        self.user = user
        self.passwd = passwd

    def sendmail(self, sender: str, to: str, msg: bytes) -> None:
        self.emails.append((sender, to, msg.decode()))
        self.count += 1

    def quit(self) -> None:
        self.quit_count += 1


class FakeSMTP_SSL(FakeSMTP):
    """ A fake version of smtplib.SMTP_SSL used for testing. """
    use_ssl = True
