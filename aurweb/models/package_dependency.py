from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import mapper

from aurweb.db import make_relationship
from aurweb.models.dependency_type import DependencyType
from aurweb.models.package import Package
from aurweb.schema import PackageDepends


class PackageDependency:
    def __init__(self, Package: Package = None,
                 DependencyType: DependencyType = None,
                 DepName: str = None, DepDesc: str = None,
                 DepCondition: str = None, DepArch: str = None):
        self.Package = Package
        if not self.Package:
            raise IntegrityError(
                statement="Foreign key PackageID cannot be null.",
                orig="PackageDependencies.PackageID",
                params=("NULL"))

        self.DependencyType = DependencyType
        if not self.DependencyType:
            raise IntegrityError(
                statement="Foreign key DepTypeID cannot be null.",
                orig="PackageDependencies.DepTypeID",
                params=("NULL"))

        self.DepName = DepName
        if not self.DepName:
            raise IntegrityError(
                statement="Column DepName cannot be null.",
                orig="PackageDependencies.DepName",
                params=("NULL"))

        self.DepDesc = DepDesc
        self.DepCondition = DepCondition
        self.DepArch = DepArch


properties = {
    "Package": make_relationship(Package, PackageDepends.c.PackageID,
                                 "package_dependencies"),
    "DependencyType": make_relationship(DependencyType,
                                        PackageDepends.c.DepTypeID,
                                        "package_dependencies")
}

mapper(PackageDependency, PackageDepends, properties=properties,
       primary_key=[PackageDepends.c.PackageID, PackageDepends.c.DepTypeID])
