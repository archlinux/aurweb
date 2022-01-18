from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import backref, relationship

from aurweb import schema
from aurweb.models.declarative import Base
from aurweb.models.package_base import PackageBase as _PackageBase
from aurweb.models.user import User as _User


class PackageVote(Base):
    __table__ = schema.PackageVotes
    __tablename__ = __table__.name
    __mapper_args__ = {
        "primary_key": [__table__.c.UsersID, __table__.c.PackageBaseID]
    }

    User = relationship(
        _User, backref=backref("package_votes", lazy="dynamic"),
        foreign_keys=[__table__.c.UsersID])

    PackageBase = relationship(
        _PackageBase, backref=backref("package_votes", lazy="dynamic",
                                      cascade="all, delete"),
        foreign_keys=[__table__.c.PackageBaseID])

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
