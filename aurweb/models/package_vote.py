from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import backref, relationship

from aurweb.models.declarative import Base
from aurweb.models.package_base import PackageBase as _PackageBase
from aurweb.models.user import User as _User


class PackageVote(Base):
    __tablename__ = "PackageVotes"

    UsersID = Column(
        Integer, ForeignKey("Users.ID", ondelete="CASCADE"),
        nullable=False)
    User = relationship(
        _User, backref=backref("package_votes", lazy="dynamic"),
        foreign_keys=[UsersID])

    PackageBaseID = Column(
        Integer, ForeignKey("PackageBases.ID", ondelete="CASCADE"),
        nullable=False)
    PackageBase = relationship(
        _PackageBase, backref=backref("package_votes", lazy="dynamic"),
        foreign_keys=[PackageBaseID])

    __mapper_args__ = {"primary_key": [UsersID, PackageBaseID]}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if not self.User and not self.UsersID:
            raise IntegrityError(
                statement="Foreign key UsersID cannot be null.",
                orig="PackageVotes.UsersID",
                params=("NULL"))

        if not self.PackageBase and not self.PackageBaseID:
            raise IntegrityError(
                statement="Foreign key PackageBaseID cannot be null.",
                orig="PackageVotes.PackageBaseID",
                params=("NULL"))

        if not self.VoteTS:
            raise IntegrityError(
                statement="Column VoteTS cannot be null.",
                orig="PackageVotes.VoteTS",
                params=("NULL"))
