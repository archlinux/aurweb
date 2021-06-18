import typing

from datetime import datetime

from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import backref, relationship

import aurweb.models.user

from aurweb.models.declarative import Base


class TUVoteInfo(Base):
    __tablename__ = "TU_VoteInfo"

    ID = Column(Integer, primary_key=True)

    SubmitterID = Column(
        Integer, ForeignKey("Users.ID", ondelete="CASCADE"),
        nullable=False)
    Submitter = relationship(
        "User", backref=backref("tu_voteinfo_set", lazy="dynamic"),
        foreign_keys=[SubmitterID])

    __mapper_args__ = {"primary_key": [ID]}

    def __init__(self,
                 Agenda: str = None,
                 User: str = None,
                 Submitted: int = None,
                 End: int = None,
                 Quorum: float = None,
                 Submitter: aurweb.models.user.User = None,
                 **kwargs):
        super().__init__(**kwargs)

        self.Agenda = Agenda
        if self.Agenda is None:
            raise IntegrityError(
                statement="Column Agenda cannot be null.",
                orig="TU_VoteInfo.Agenda",
                params=("NULL"))

        self.User = User
        if self.User is None:
            raise IntegrityError(
                statement="Column User cannot be null.",
                orig="TU_VoteInfo.User",
                params=("NULL"))

        self.Submitted = Submitted
        if self.Submitted is None:
            raise IntegrityError(
                statement="Column Submitted cannot be null.",
                orig="TU_VoteInfo.Submitted",
                params=("NULL"))

        self.End = End
        if self.End is None:
            raise IntegrityError(
                statement="Column End cannot be null.",
                orig="TU_VoteInfo.End",
                params=("NULL"))

        if Quorum is None:
            raise IntegrityError(
                statement="Column Quorum cannot be null.",
                orig="TU_VoteInfo.Quorum",
                params=("NULL"))
        self.Quorum = Quorum

        self.Submitter = Submitter
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
        return float(attr) if key == "Quorum" else attr

    def is_running(self):
        return self.End > int(datetime.utcnow().timestamp())
