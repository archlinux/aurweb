import typing

from datetime import datetime

from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import backref, relationship

from aurweb.models.declarative import Base
from aurweb.models.user import User as _User


class TUVoteInfo(Base):
    __tablename__ = "TU_VoteInfo"

    ID = Column(Integer, primary_key=True)

    SubmitterID = Column(
        Integer, ForeignKey("Users.ID", ondelete="CASCADE"),
        nullable=False)
    Submitter = relationship(
        _User, backref=backref("tu_voteinfo_set", lazy="dynamic"),
        foreign_keys=[SubmitterID])

    __mapper_args__ = {"primary_key": [ID]}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if self.Agenda is None:
            raise IntegrityError(
                statement="Column Agenda cannot be null.",
                orig="TU_VoteInfo.Agenda",
                params=("NULL"))

        if self.User is None:
            raise IntegrityError(
                statement="Column User cannot be null.",
                orig="TU_VoteInfo.User",
                params=("NULL"))

        if self.Submitted is None:
            raise IntegrityError(
                statement="Column Submitted cannot be null.",
                orig="TU_VoteInfo.Submitted",
                params=("NULL"))

        if self.End is None:
            raise IntegrityError(
                statement="Column End cannot be null.",
                orig="TU_VoteInfo.End",
                params=("NULL"))

        if self.Quorum is None:
            raise IntegrityError(
                statement="Column Quorum cannot be null.",
                orig="TU_VoteInfo.Quorum",
                params=("NULL"))

        if not self.Submitter:
            raise IntegrityError(
                statement="Foreign key SubmitterID cannot be null.",
                orig="TU_VoteInfo.SubmitterID",
                params=("NULL"))

    def __setattr__(self, key: str, value: typing.Any):
        """ Customize setattr to stringify any Quorum keys given. """
        if key == "Quorum":
            value = str(value)
        return super().__setattr__(key, value)

    def __getattribute__(self, key: str):
        """ Customize getattr to floatify any fetched Quorum values. """
        attr = super().__getattribute__(key)
        if attr is None:
            return attr
        elif key == "Quorum":
            return float(attr)
        return attr

    def is_running(self):
        return self.End > int(datetime.utcnow().timestamp())

    def total_votes(self):
        return self.Yes + self.No + self.Abstain
