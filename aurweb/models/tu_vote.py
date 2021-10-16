from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import backref, relationship

from aurweb.models.declarative import Base
from aurweb.models.tu_voteinfo import TUVoteInfo as _TUVoteInfo
from aurweb.models.user import User as _User


class TUVote(Base):
    __tablename__ = "TU_Votes"

    VoteID = Column(Integer, ForeignKey("TU_VoteInfo.ID", ondelete="CASCADE"),
                    nullable=False)
    VoteInfo = relationship(
        _TUVoteInfo, backref=backref("tu_votes", lazy="dynamic"),
        foreign_keys=[VoteID])

    UserID = Column(Integer, ForeignKey("Users.ID", ondelete="CASCADE"),
                    nullable=False)
    User = relationship(
        _User, backref=backref("tu_votes", lazy="dynamic"),
        foreign_keys=[UserID])

    __mapper_args__ = {"primary_key": [VoteID, UserID]}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if not self.VoteInfo and not self.VoteID:
            raise IntegrityError(
                statement="Foreign key VoteID cannot be null.",
                orig="TU_Votes.VoteID",
                params=("NULL"))

        if not self.User and not self.UserID:
            raise IntegrityError(
                statement="Foreign key UserID cannot be null.",
                orig="TU_Votes.UserID",
                params=("NULL"))
