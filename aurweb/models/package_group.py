from sqlalchemy.orm import mapper
from sqlalchemy.exc import IntegrityError

from aurweb.db import make_relationship
from aurweb.models.group import Group
from aurweb.models.package import Package
from aurweb.schema import PackageGroups


class PackageGroup:
    def __init__(self, Package: Package = None, Group: Group = None):
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


properties = {
    "Package": make_relationship(Package,
                                 PackageGroups.c.PackageID,
                                 "package_group",
                                 uselist=False),
    "Group": make_relationship(Group,
                               PackageGroups.c.GroupID,
                               "package_group",
                               uselist=False)
}

mapper(PackageGroup, PackageGroups, properties=properties,
       primary_key=[PackageGroups.c.PackageID, PackageGroups.c.GroupID])
