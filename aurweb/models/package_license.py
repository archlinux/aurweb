from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import backref, relationship

from aurweb.models.declarative import Base
from aurweb.models.license import License as _License
from aurweb.models.package import Package as _Package


class PackageLicense(Base):
    __tablename__ = "PackageLicenses"

    PackageID = Column(
        Integer, ForeignKey("Packages.ID", ondelete="CASCADE"),
        primary_key=True, nullable=True)
    Package = relationship(
        _Package, backref=backref("package_licenses", lazy="dynamic",
                                  cascade="all, delete"),
        foreign_keys=[PackageID])

    LicenseID = Column(
        Integer, ForeignKey("Licenses.ID", ondelete="CASCADE"),
        primary_key=True, nullable=True)
    License = relationship(
        _License, backref=backref("package_licenses", lazy="dynamic",
                                  cascade="all, delete"),
        foreign_keys=[LicenseID])

    __mapper_args__ = {"primary_key": [PackageID, LicenseID]}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if not self.Package and not self.PackageID:
            raise IntegrityError(
                statement="Primary key PackageID cannot be null.",
                orig="PackageLicenses.PackageID",
                params=("NULL"))

        if not self.License and not self.LicenseID:
            raise IntegrityError(
                statement="Primary key LicenseID cannot be null.",
                orig="PackageLicenses.LicenseID",
                params=("NULL"))
