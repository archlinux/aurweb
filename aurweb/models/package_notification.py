from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import backref, relationship

from aurweb.models.declarative import Base
from aurweb.models.package_base import PackageBase as _PackageBase
from aurweb.models.user import User as _User


class PackageNotification(Base):
    __tablename__ = "PackageNotifications"

    UserID = Column(
        Integer, ForeignKey("Users.ID", ondelete="CASCADE"),
        nullable=False)
    User = relationship(
        _User, backref=backref("notifications", lazy="dynamic"),
        foreign_keys=[UserID])

    PackageBaseID = Column(
        Integer, ForeignKey("PackageBases.ID", ondelete="CASCADE"),
        nullable=False)
    PackageBase = relationship(
        _PackageBase,
        backref=backref("notifications", lazy="dynamic"),
        foreign_keys=[PackageBaseID])

    __mapper_args__ = {"primary_key": [UserID, PackageBaseID]}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if not self.User and not self.UserID:
            raise IntegrityError(
                statement="Foreign key UserID cannot be null.",
                orig="PackageNotifications.UserID",
                params=("NULL"))

        if not self.PackageBase and not self.PackageBaseID:
            raise IntegrityError(
                statement="Foreign key PackageBaseID cannot be null.",
                orig="PackageNotifications.PackageBaseID",
                params=("NULL"))
