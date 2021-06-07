from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import backref, relationship

from aurweb.db import make_random_value, query
from aurweb.models.declarative import Base
from aurweb.models.user import User


class Session(Base):
    __tablename__ = "Sessions"

    UsersID = Column(
        Integer, ForeignKey("Users.ID", ondelete="CASCADE"),
        nullable=False)
    User = relationship(
        "User", backref=backref("session", uselist=False),
        foreign_keys=[UsersID])

    __mapper_args__ = {"primary_key": [UsersID]}

    def __init__(self, **kwargs):
        self.UsersID = kwargs.get("UsersID")
        if not query(User, User.ID == self.UsersID).first():
            raise IntegrityError(
                statement="Foreign key UsersID cannot be null.",
                orig="Sessions.UsersID",
                params=("NULL"))

        self.SessionID = kwargs.get("SessionID")
        self.LastUpdateTS = kwargs.get("LastUpdateTS")


def generate_unique_sid():
    return make_random_value(Session, Session.SessionID)
