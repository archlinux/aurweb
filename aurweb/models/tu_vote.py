from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import backref, relationship

from aurweb import schema
from aurweb.models.declarative import Base
from aurweb.models.tu_voteinfo import TUVoteInfo as _TUVoteInfo
from aurweb.models.user import User as _User


class TUVote(Base):
    __table__ = schema.TU_Votes
    __tablename__ = __table__.name
    __mapper_args__ = {
        "primary_key": [__table__.c.VoteID, __table__.c.UserID]
    }

    VoteInfo = relationship(
        _TUVoteInfo, backref=backref("tu_votes", lazy="dynamic"),
        foreign_keys=[__table__.c.VoteID])

    User = relationship(
        _User, backref=backref("tu_votes", lazy="dynamic"),
        foreign_keys=[__table__.c.UserID])

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
