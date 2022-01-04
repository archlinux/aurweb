from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import backref, relationship

from aurweb import schema
from aurweb.models.declarative import Base
from aurweb.models.group import Group as _Group
from aurweb.models.package import Package as _Package


class PackageGroup(Base):
    __table__ = schema.PackageGroups
    __tablename__ = __table__.name
    __mapper_args__ = {
        "primary_key": [__table__.c.PackageID, __table__.c.GroupID]
    }

    Package = relationship(
        _Package, backref=backref("package_groups", lazy="dynamic",
                                  cascade="all, delete"),
        foreign_keys=[__table__.c.PackageID])

    Group = relationship(
        _Group, backref=backref("package_groups", lazy="dynamic",
                                cascade="all, delete"),
        foreign_keys=[__table__.c.GroupID])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if not self.Package and not self.PackageID:
            raise IntegrityError(
                statement="Primary key PackageID cannot be null.",
                orig="PackageGroups.PackageID",
                params=("NULL"))

        if not self.Group and not self.GroupID:
            raise IntegrityError(
                statement="Primary key GroupID cannot be null.",
                orig="PackageGroups.GroupID",
                params=("NULL"))
