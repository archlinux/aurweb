from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import backref, relationship

import aurweb.models.package_base
import aurweb.models.user

from aurweb.models.declarative import Base


class PackageVote(Base):
    __tablename__ = "PackageVotes"

    UsersID = Column(
        Integer, ForeignKey("Users.ID", ondelete="CASCADE"),
        nullable=False)
    User = relationship(
        "User", backref=backref("package_votes", lazy="dynamic"),
        foreign_keys=[UsersID])

    PackageBaseID = Column(
        Integer, ForeignKey("PackageBases.ID", ondelete="CASCADE"),
        nullable=False)
    PackageBase = relationship(
        "PackageBase", backref=backref("package_votes", lazy="dynamic"),
        foreign_keys=[PackageBaseID])

    __mapper_args__ = {"primary_key": [UsersID, PackageBaseID]}

    def __init__(self,
                 User: aurweb.models.user.User = None,
                 PackageBase: aurweb.models.package_base.PackageBase = None,
                 VoteTS: int = None):
        self.User = User
        if not self.User:
            raise IntegrityError(
                statement="Foreign key UsersID cannot be null.",
                orig="PackageVotes.UsersID",
                params=("NULL"))

        self.PackageBase = PackageBase
        if not self.PackageBase:
            raise IntegrityError(
                statement="Foreign key PackageBaseID cannot be null.",
                orig="PackageVotes.PackageBaseID",
                params=("NULL"))

        self.VoteTS = VoteTS
        if not self.VoteTS:
            raise IntegrityError(
                statement="Column VoteTS cannot be null.",
                orig="PackageVotes.VoteTS",
                params=("NULL"))
