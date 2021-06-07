from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import backref, relationship

import aurweb.models.group
import aurweb.models.package

from aurweb.models.declarative import Base


class PackageGroup(Base):
    __tablename__ = "PackageGroups"

    PackageID = Column(Integer, ForeignKey("Packages.ID", ondelete="CASCADE"),
                       primary_key=True, nullable=True)
    Package = relationship(
        "Package", backref=backref("package_groups", lazy="dynamic"),
        foreign_keys=[PackageID])

    GroupID = Column(Integer, ForeignKey("Groups.ID", ondelete="CASCADE"),
                     primary_key=True, nullable=True)
    Group = relationship(
        "Group", backref=backref("package_groups", lazy="dynamic"),
        foreign_keys=[GroupID])

    __mapper_args__ = {"primary_key": [PackageID, GroupID]}

    def __init__(self,
                 Package: aurweb.models.package.Package = None,
                 Group: aurweb.models.group.Group = None):
        self.Package = Package
        if not self.Package:
            raise IntegrityError(
                statement="Primary key PackageID cannot be null.",
                orig="PackageGroups.PackageID",
                params=("NULL"))

        self.Group = Group
        if not self.Group:
            raise IntegrityError(
                statement="Primary key GroupID cannot be null.",
                orig="PackageGroups.GroupID",
                params=("NULL"))
