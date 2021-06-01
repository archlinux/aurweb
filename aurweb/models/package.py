from sqlalchemy.orm import mapper

from aurweb.db import make_relationship
from aurweb.models.package_base import PackageBase
from aurweb.schema import Packages


class Package:
    def __init__(self,
                 PackageBase: PackageBase = None,
                 Name: str = None, Version: str = None,
                 Description: str = None, URL: str = None):
        self.PackageBase = PackageBase
        self.Name = Name
        self.Version = Version
        self.Description = Description
        self.URL = URL


mapper(Package, Packages, properties={
    "PackageBase": make_relationship(PackageBase,
                                     Packages.c.PackageBaseID,
                                     "package", uselist=False)
})
