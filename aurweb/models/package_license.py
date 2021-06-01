from sqlalchemy.orm import mapper

from aurweb.db import make_relationship
from aurweb.models.license import License
from aurweb.models.package import Package
from aurweb.schema import PackageLicenses


class PackageLicense:
    def __init__(self, Package: Package = None, License: License = None):
        self.Package = Package
        self.License = License


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
