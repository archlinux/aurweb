import hashlib

from datetime import datetime

import bcrypt

from fastapi import Request
from sqlalchemy import Column, ForeignKey, Integer, String, text
from sqlalchemy.orm import backref, relationship

import aurweb.config
import aurweb.models.account_type
import aurweb.schema

from aurweb.models.ban import is_banned
from aurweb.models.declarative import Base


class User(Base):
    """ An ORM model of a single Users record. """
    __tablename__ = "Users"

    ID = Column(Integer, primary_key=True)

    AccountTypeID = Column(
        Integer, ForeignKey("AccountTypes.ID", ondelete="NO ACTION"),
        nullable=False, server_default=text("1"))
    AccountType = relationship(
        "AccountType",
        backref=backref("users", lazy="dynamic"),
        foreign_keys=[AccountTypeID],
        uselist=False)

    Passwd = Column(String(255), default=str())

    __mapper_args__ = {"primary_key": [ID]}

    # High-level variables used to track authentication (not in DB).
    authenticated = False
    nonce = None

    def __init__(self, Passwd: str = str(), **kwargs):
        super().__init__(**kwargs)

        if Passwd:
            self.update_password(Passwd)

    def update_password(self, password, salt_rounds=12):
        self.Passwd = bcrypt.hashpw(
            password.encode(),
            bcrypt.gensalt(rounds=salt_rounds)).decode()

    @staticmethod
    def minimum_passwd_length():
        return aurweb.config.getint("options", "passwd_min_len")

    def is_authenticated(self):
        """ Return internal authenticated state. """
        return self.authenticated

    def valid_password(self, password: str):
        """ Check authentication against a given password. """
        if password is None:
            return False

        password_is_valid = False

        try:
            password_is_valid = bcrypt.checkpw(password.encode(),
                                               self.Passwd.encode())
        except ValueError:
            pass

        # If our Salt column is not empty, we're using a legacy password.
        if not password_is_valid and self.Salt != str():
            # Try to login with legacy method.
            password_is_valid = hashlib.md5(
                f"{self.Salt}{password}".encode()
            ).hexdigest() == self.Passwd

            # We got here, we passed the legacy authentication.
            # Update the password to our modern hash style.
            if password_is_valid:
                self.update_password(password)

        return password_is_valid

    def _login_approved(self, request: Request):
        return not is_banned(request) and not self.Suspended

    def login(self, request: Request, password: str, session_time=0):
        """ Login and authenticate a request. """

        from aurweb.db import session
        from aurweb.models.session import Session, generate_unique_sid

        if not self._login_approved(request):
            return None

        self.authenticated = self.valid_password(password)
        if not self.authenticated:
            return None

        self.LastLogin = now_ts = datetime.utcnow().timestamp()
        self.LastLoginIPAddress = request.client.host
        session.commit()

        session_ts = now_ts + (
            session_time if session_time
            else aurweb.config.getint("options", "login_timeout")
        )

        sid = None

        if not self.session:
            sid = generate_unique_sid()
            self.session = Session(UsersID=self.ID, SessionID=sid,
                                   LastUpdateTS=session_ts)
            session.add(self.session)
        else:
            last_updated = self.session.LastUpdateTS
            if last_updated and last_updated < now_ts:
                self.session.SessionID = sid = generate_unique_sid()
            else:
                # Session is still valid; retrieve the current SID.
                sid = self.session.SessionID

            self.session.LastUpdateTS = session_ts

        session.commit()

        request.cookies["AURSID"] = self.session.SessionID
        return self.session.SessionID

    def has_credential(self, credential: str, approved: list = tuple()):
        import aurweb.auth
        cred = getattr(aurweb.auth, credential)
        return aurweb.auth.has_credential(self, cred, approved)

    def logout(self, request):
        from aurweb.db import session

        del request.cookies["AURSID"]
        self.authenticated = False
        if self.session:
            session.delete(self.session)
            session.commit()

    def __repr__(self):
        return "<User(ID='%s', AccountType='%s', Username='%s')>" % (
            self.ID, str(self.AccountType), self.Username)
