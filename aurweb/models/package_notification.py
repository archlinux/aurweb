from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import backref, relationship

from aurweb import schema
from aurweb.models.declarative import Base
from aurweb.models.package_base import PackageBase as _PackageBase
from aurweb.models.user import User as _User


class PackageNotification(Base):
    __table__ = schema.PackageNotifications
    __tablename__ = __table__.name
    __mapper_args__ = {
        "primary_key": [__table__.c.UserID, __table__.c.PackageBaseID]
    }

    User = relationship(
        _User, backref=backref("notifications", lazy="dynamic",
                               cascade="all, delete"),
        foreign_keys=[__table__.c.UserID])

    PackageBase = relationship(
        _PackageBase,
        backref=backref("notifications", lazy="dynamic",
                        cascade="all, delete"),
        foreign_keys=[__table__.c.PackageBaseID])

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
