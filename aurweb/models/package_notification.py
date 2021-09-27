from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import backref, relationship

import aurweb.models.package_base
import aurweb.models.user

from aurweb.models.declarative import Base


class PackageNotification(Base):
    __tablename__ = "PackageNotifications"

    UserID = Column(
        Integer, ForeignKey("Users.ID", ondelete="CASCADE"),
        nullable=False)
    User = relationship(
        "User", backref=backref("notifications", lazy="dynamic"),
        foreign_keys=[UserID])

    PackageBaseID = Column(
        Integer, ForeignKey("PackageBases.ID", ondelete="CASCADE"),
        nullable=False)
    PackageBase = relationship(
        "PackageBase",
        backref=backref("notifications", lazy="dynamic"),
        foreign_keys=[PackageBaseID])

    __mapper_args__ = {"primary_key": [UserID, PackageBaseID]}

    def __init__(self,
                 User: aurweb.models.user.User = None,
                 PackageBase: aurweb.models.package_base.PackageBase = None,
                 NotificationTS: int = None):
        self.User = User
        if not self.User:
            raise IntegrityError(
                statement="Foreign key UserID cannot be null.",
                orig="PackageNotifications.UserID",
                params=("NULL"))

        self.PackageBase = PackageBase
        if not self.PackageBase:
            raise IntegrityError(
                statement="Foreign key PackageBaseID cannot be null.",
                orig="PackageNotifications.PackageBaseID",
                params=("NULL"))
