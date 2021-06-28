from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import backref, relationship

import aurweb.db
import aurweb.models.package_base

from aurweb.models.declarative import Base


class Package(Base):
    __tablename__ = "Packages"

    ID = Column(Integer, primary_key=True)

    PackageBaseID = Column(
        Integer, ForeignKey("PackageBases.ID", ondelete="CASCADE"),
        nullable=False)
    PackageBase = relationship(
        "PackageBase", backref=backref("packages", lazy="dynamic"),
        foreign_keys=[PackageBaseID])

    __mapper_args__ = {"primary_key": [ID]}

    def __init__(self,
                 PackageBase: aurweb.models.package_base.PackageBase = None,
                 Name: str = None,
                 Version: str = None,
                 Description: str = None,
                 URL: str = None):
        self.PackageBase = PackageBase
        if not self.PackageBase:
            raise IntegrityError(
                statement="Foreign key PackageBaseID cannot be null.",
                orig="Packages.PackageBaseID",
                params=("NULL"))

        self.Name = Name
        if not self.Name:
            raise IntegrityError(
                statement="Column Name cannot be null.",
                orig="Packages.Name",
                params=("NULL"))

        self.Version = Version
        self.Description = Description
        self.URL = URL
