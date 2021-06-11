from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import backref, relationship

import aurweb.models.package_base
import aurweb.models.user

from aurweb.models.declarative import Base


class PackageComaintainer(Base):
    __tablename__ = "PackageComaintainers"

    UsersID = Column(
        Integer, ForeignKey("Users.ID", ondelete="CASCADE"),
        nullable=False)
    User = relationship(
        "User", backref=backref("comaintained", lazy="dynamic"),
        foreign_keys=[UsersID])

    PackageBaseID = Column(
        Integer, ForeignKey("PackageBases.ID", ondelete="CASCADE"),
        nullable=False)
    PackageBase = relationship(
        "PackageBase", backref=backref("comaintainers", lazy="dynamic"),
        foreign_keys=[PackageBaseID])

    __mapper_args__ = {"primary_key": [UsersID, PackageBaseID]}

    def __init__(self,
                 User: aurweb.models.user.User = None,
                 PackageBase: aurweb.models.package_base.PackageBase = None,
                 Priority: int = None):
        self.User = User
        if not self.User:
            raise IntegrityError(
                statement="Foreign key UsersID cannot be null.",
                orig="PackageComaintainers.UsersID",
                params=("NULL"))

        self.PackageBase = PackageBase
        if not self.PackageBase:
            raise IntegrityError(
                statement="Foreign key PackageBaseID cannot be null.",
                orig="PackageComaintainers.PackageBaseID",
                params=("NULL"))

        self.Priority = Priority
        if not self.Priority:
            raise IntegrityError(
                statement="Column Priority cannot be null.",
                orig="PackageComaintainers.Priority",
                params=("NULL"))
