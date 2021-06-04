from sqlalchemy.orm import mapper
from sqlalchemy.exc import IntegrityError

from aurweb.db import make_relationship
from aurweb.models.license import License
from aurweb.models.package import Package
from aurweb.schema import PackageLicenses


class PackageLicense:
    def __init__(self, Package: Package = None, License: License = None):
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


properties = {
    "Package": make_relationship(Package,
                                 PackageLicenses.c.PackageID,
                                 "package_license",
                                 uselist=False),
    "License": make_relationship(License,
                                 PackageLicenses.c.LicenseID,
                                 "package_license",
                                 uselist=False)


}

mapper(PackageLicense, PackageLicenses, properties=properties,
       primary_key=[PackageLicenses.c.PackageID, PackageLicenses.c.LicenseID])
