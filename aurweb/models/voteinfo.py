import typing

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import backref, relationship

from aurweb import schema, time
from aurweb.models.declarative import Base
from aurweb.models.user import User as _User


class VoteInfo(Base):
    __table__ = schema.VoteInfo
    __tablename__ = __table__.name
    __mapper_args__ = {"primary_key": [__table__.c.ID]}

    Submitter = relationship(
        _User,
        backref=backref("voteinfo_set", lazy="dynamic"),
        foreign_keys=[__table__.c.SubmitterID],
    )

    def __init__(self, **kwargs):
        # Default Quorum, Yes, No and Abstain columns to 0.
        for col in ("Quorum", "Yes", "No", "Abstain"):
            if col not in kwargs:
                kwargs.update({col: 0})

        super().__init__(**kwargs)

        if self.Agenda is None:
            raise IntegrityError(
                statement="Column Agenda cannot be null.",
                orig="VoteInfo.Agenda",
                params=("NULL"),
            )

        if self.User is None:
            raise IntegrityError(
                statement="Column User cannot be null.",
                orig="VoteInfo.User",
                params=("NULL"),
            )

        if self.Submitted is None:
            raise IntegrityError(
                statement="Column Submitted cannot be null.",
                orig="VoteInfo.Submitted",
                params=("NULL"),
            )

        if self.End is None:
            raise IntegrityError(
                statement="Column End cannot be null.",
                orig="VoteInfo.End",
                params=("NULL"),
            )

        if not self.Submitter:
            raise IntegrityError(
                statement="Foreign key SubmitterID cannot be null.",
                orig="VoteInfo.SubmitterID",
                params=("NULL"),
            )

    def __setattr__(self, key: str, value: typing.Any):
        """Customize setattr to stringify any Quorum keys given."""
        if key == "Quorum":
            value = str(value)
        return super().__setattr__(key, value)

    def __getattribute__(self, key: str):
        """Customize getattr to floatify any fetched Quorum values."""
        attr = super().__getattribute__(key)
        if key == "Quorum":
            return float(attr)
        return attr

    def is_running(self):
        return self.End > time.utcnow()

    def total_votes(self):
        return self.Yes + self.No + self.Abstain
