from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import backref, mapper, relationship

from aurweb.db import make_random_value, query
from aurweb.models.user import User
from aurweb.schema import Sessions


class Session:
    def __init__(self, **kwargs):
        self.UsersID = kwargs.get("UsersID")
        if not query(User, User.ID == self.UsersID).first():
            raise IntegrityError(
                statement="Foreign key UsersID cannot be null.",
                orig="Sessions.UsersID",
                params=("NULL"))

        self.SessionID = kwargs.get("SessionID")
        self.LastUpdateTS = kwargs.get("LastUpdateTS")


mapper(Session, Sessions, primary_key=[Sessions.c.SessionID], properties={
    "User": relationship(User, backref=backref("session",
                                               uselist=False))
})


def generate_unique_sid():
    return make_random_value(Session, Session.SessionID)
