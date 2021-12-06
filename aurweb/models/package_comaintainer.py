from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import backref, relationship

from aurweb import schema
from aurweb.models.declarative import Base
from aurweb.models.package_base import PackageBase as _PackageBase
from aurweb.models.user import User as _User


class PackageComaintainer(Base):
    __table__ = schema.PackageComaintainers
    __tablename__ = __table__.name
    __mapper_args__ = {
        "primary_key": [__table__.c.UsersID, __table__.c.PackageBaseID]
    }

    User = relationship(
        _User, backref=backref("comaintained", lazy="dynamic",
                               cascade="all, delete"),
        foreign_keys=[__table__.c.UsersID])

    PackageBase = relationship(
        _PackageBase, backref=backref("comaintainers", lazy="dynamic",
                                      cascade="all, delete"),
        foreign_keys=[__table__.c.PackageBaseID])

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
