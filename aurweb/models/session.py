from sqlalchemy import Column, Integer
from sqlalchemy.orm import backref, mapper, relationship

from aurweb.db import make_random_value
from aurweb.models.user import User
from aurweb.schema import Sessions


class Session:
    UsersID = Column(Integer, nullable=True)

    def __init__(self, **kwargs):
        self.UsersID = kwargs.get("UsersID")
        self.SessionID = kwargs.get("SessionID")
        self.LastUpdateTS = kwargs.get("LastUpdateTS")


mapper(Session, Sessions, primary_key=[Sessions.c.SessionID], properties={
    "User": relationship(User, backref=backref("session",
                                               uselist=False))
})


def generate_unique_sid():
    return make_random_value(Session, Session.SessionID)
