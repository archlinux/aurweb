from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import backref, relationship

import aurweb.models.tu_voteinfo
import aurweb.models.user

from aurweb.models.declarative import Base


class TUVote(Base):
    __tablename__ = "TU_Votes"

    VoteID = Column(Integer, ForeignKey("TU_VoteInfo.ID", ondelete="CASCADE"),
                    nullable=False)
    VoteInfo = relationship(
        "TUVoteInfo", backref=backref("tu_votes", lazy="dynamic"),
        foreign_keys=[VoteID])

    UserID = Column(Integer, ForeignKey("Users.ID", ondelete="CASCADE"),
                    nullable=False)
    User = relationship(
        "User", backref=backref("tu_votes", lazy="dynamic"),
        foreign_keys=[UserID])

    __mapper_args__ = {"primary_key": [VoteID, UserID]}

    def __init__(self,
                 VoteInfo: aurweb.models.tu_voteinfo.TUVoteInfo = None,
                 User: aurweb.models.user.User = None):
        self.VoteInfo = VoteInfo
        if self.VoteInfo is None:
            raise IntegrityError(
                statement="Foreign key VoteID cannot be null.",
                orig="TU_Votes.VoteID",
                params=("NULL"))

        self.User = User
        if self.User is None:
            raise IntegrityError(
                statement="Foreign key UserID cannot be null.",
                orig="TU_Votes.UserID",
                params=("NULL"))
