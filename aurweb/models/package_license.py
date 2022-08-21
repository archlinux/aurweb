from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import backref, relationship

from aurweb import schema
from aurweb.models.declarative import Base
from aurweb.models.license import License as _License
from aurweb.models.package import Package as _Package


class PackageLicense(Base):
    __table__ = schema.PackageLicenses
    __tablename__ = __table__.name
    __mapper_args__ = {"primary_key": [__table__.c.PackageID, __table__.c.LicenseID]}

    Package = relationship(
        _Package,
        backref=backref("package_licenses", lazy="dynamic", cascade="all, delete"),
        foreign_keys=[__table__.c.PackageID],
    )

    License = relationship(
        _License,
        backref=backref("package_licenses", lazy="dynamic", cascade="all, delete"),
        foreign_keys=[__table__.c.LicenseID],
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if not self.Package and not self.PackageID:
            raise IntegrityError(
                statement="Primary key PackageID cannot be null.",
                orig="PackageLicenses.PackageID",
                params=("NULL"),
            )

        if not self.License and not self.LicenseID:
            raise IntegrityError(
                statement="Primary key LicenseID cannot be null.",
                orig="PackageLicenses.LicenseID",
                params=("NULL"),
            )
