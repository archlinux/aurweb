from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import backref, relationship

from aurweb.models.declarative import Base
from aurweb.models.package_base import PackageBase as _PackageBase
from aurweb.models.user import User as _User


class PackageComaintainer(Base):
    __tablename__ = "PackageComaintainers"

    UsersID = Column(
        Integer, ForeignKey("Users.ID", ondelete="CASCADE"),
        nullable=False)
    User = relationship(
        _User, backref=backref("comaintained", lazy="dynamic"),
        foreign_keys=[UsersID])

    PackageBaseID = Column(
        Integer, ForeignKey("PackageBases.ID", ondelete="CASCADE"),
        nullable=False)
    PackageBase = relationship(
        _PackageBase, backref=backref("comaintainers", lazy="dynamic"),
        foreign_keys=[PackageBaseID])

    __mapper_args__ = {"primary_key": [UsersID, PackageBaseID]}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if not self.User and not self.UsersID:
            raise IntegrityError(
                statement="Foreign key UsersID cannot be null.",
                orig="PackageComaintainers.UsersID",
                params=("NULL"))

        if not self.PackageBase and not self.PackageBaseID:
            raise IntegrityError(
                statement="Foreign key PackageBaseID cannot be null.",
                orig="PackageComaintainers.PackageBaseID",
                params=("NULL"))

        if not self.Priority:
            raise IntegrityError(
                statement="Column Priority cannot be null.",
                orig="PackageComaintainers.Priority",
                params=("NULL"))
