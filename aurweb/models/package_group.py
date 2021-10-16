from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import backref, relationship

from aurweb.models.declarative import Base
from aurweb.models.group import Group as _Group
from aurweb.models.package import Package as _Package


class PackageGroup(Base):
    __tablename__ = "PackageGroups"

    PackageID = Column(Integer, ForeignKey("Packages.ID", ondelete="CASCADE"),
                       primary_key=True, nullable=True)
    Package = relationship(
        _Package, backref=backref("package_groups", lazy="dynamic"),
        foreign_keys=[PackageID])

    GroupID = Column(Integer, ForeignKey("Groups.ID", ondelete="CASCADE"),
                     primary_key=True, nullable=True)
    Group = relationship(
        _Group, backref=backref("package_groups", lazy="dynamic"),
        foreign_keys=[GroupID])

    __mapper_args__ = {"primary_key": [PackageID, GroupID]}

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
