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
        self.DependencyType = DependencyType
        self.DepName = DepName  # nullable=False
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
