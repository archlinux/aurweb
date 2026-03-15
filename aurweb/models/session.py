from sqlalchemy import exists, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import backref, relationship

from aurweb import db, schema
from aurweb.models.declarative import Base
from aurweb.models.user import User as _User


class Session(Base):
    __table__ = schema.Sessions
    __tablename__ = __table__.name
    __mapper_args__ = {"primary_key": [__table__.c.UsersID]}

    User = relationship(
        _User,
        backref=backref("session", cascade="all, delete", uselist=False),
        foreign_keys=[__table__.c.UsersID],
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # We'll try to either use UsersID or User.ID if we can.
        # If neither exist, an AttributeError is raised, in which case
        # we set the uid to 0, which triggers IntegrityError below.
        try:
            uid = self.UsersID or self.User.ID
        except AttributeError:
            uid = 0

        user_exists = (
            db.get_session().execute(select(exists().where(_User.ID == uid))).scalar()
        )
        if not user_exists:
            raise IntegrityError(
                statement=(
                    "Foreign key UsersID cannot be null and must be a valid user's ID."
                ),
                orig="Sessions.UsersID",
                params=("NULL"),
            )


def generate_unique_sid():
    return db.make_random_value(Session, Session.SessionID, 32)
