from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import backref, relationship

import aurweb.models.license
import aurweb.models.package

from aurweb.models.declarative import Base


class PackageLicense(Base):
    __tablename__ = "PackageLicenses"

    PackageID = Column(
        Integer, ForeignKey("Packages.ID", ondelete="CASCADE"),
        primary_key=True, nullable=True)
    Package = relationship(
        "Package", backref=backref("package_license", uselist=False),
        foreign_keys=[PackageID])

    LicenseID = Column(
        Integer, ForeignKey("Licenses.ID", ondelete="CASCADE"),
        primary_key=True, nullable=True)
    License = relationship(
        "License", backref=backref("package_license", uselist=False),
        foreign_keys=[LicenseID])

    __mapper_args__ = {"primary_key": [PackageID, LicenseID]}

    def __init__(self,
                 Package: aurweb.models.package.Package = None,
                 License: aurweb.models.license.License = None):
        self.Package = Package
        if not self.Package:
            raise IntegrityError(
                statement="Primary key PackageID cannot be null.",
                orig="PackageLicenses.PackageID",
                params=("NULL"))

        self.License = License
        if not self.License:
            raise IntegrityError(
                statement="Primary key LicenseID cannot be null.",
                orig="PackageLicenses.LicenseID",
                params=("NULL"))
