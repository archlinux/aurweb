from sqlalchemy.orm import mapper

from aurweb.db import make_relationship
from aurweb.models.package import Package
from aurweb.models.relation_type import RelationType
from aurweb.schema import PackageRelations


class PackageRelation:
    def __init__(self, Package: Package = None,
                 RelationType: RelationType = None,
                 RelName: str = None, RelCondition: str = None,
                 RelArch: str = None):
        self.Package = Package
        self.RelationType = RelationType
        self.RelName = RelName  # nullable=False
        self.RelCondition = RelCondition
        self.RelArch = RelArch


properties = {
    "Package": make_relationship(Package, PackageRelations.c.PackageID,
                                 "package_relations"),
    "RelationType": make_relationship(RelationType,
                                      PackageRelations.c.RelTypeID,
                                      "package_relations")
}

mapper(PackageRelation, PackageRelations, properties=properties,
       primary_key=[
           PackageRelations.c.PackageID,
           PackageRelations.c.RelTypeID
       ])
