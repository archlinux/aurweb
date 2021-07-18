from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import backref, relationship

import aurweb.db
import aurweb.models.package
import aurweb.models.relation_type

from aurweb.models.declarative import Base


class PackageRelation(Base):
    __tablename__ = "PackageRelations"

    PackageID = Column(
        Integer, ForeignKey("Packages.ID", ondelete="CASCADE"),
        nullable=False)
    Package = relationship(
        "Package", backref=backref("package_relations", lazy="dynamic"),
        foreign_keys=[PackageID])

    RelTypeID = Column(
        Integer, ForeignKey("RelationTypes.ID", ondelete="CASCADE"),
        nullable=False)
    RelationType = relationship(
        "RelationType", backref=backref("package_relations", lazy="dynamic"),
        foreign_keys=[RelTypeID])

    RelName = Column(String(255), unique=True)

    __mapper_args__ = {"primary_key": [PackageID, RelName]}

    def __init__(self,
                 Package: aurweb.models.package.Package = None,
                 RelationType: aurweb.models.relation_type.RelationType = None,
                 RelName: str = None, RelCondition: str = None,
                 RelArch: str = None):
        self.Package = Package
        if not self.Package:
            raise IntegrityError(
                statement="Foreign key PackageID cannot be null.",
                orig="PackageRelations.PackageID",
                params=("NULL"))

        self.RelationType = RelationType
        if not self.RelationType:
            raise IntegrityError(
                statement="Foreign key RelTypeID cannot be null.",
                orig="PackageRelations.RelTypeID",
                params=("NULL"))

        self.RelName = RelName  # nullable=False
        if not self.RelName:
            raise IntegrityError(
                statement="Column RelName cannot be null.",
                orig="PackageRelations.RelName",
                params=("NULL"))

        self.RelCondition = RelCondition
        self.RelArch = RelArch
