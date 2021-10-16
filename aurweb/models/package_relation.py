from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import backref, relationship

from aurweb.models.declarative import Base
from aurweb.models.package import Package as _Package
from aurweb.models.relation_type import RelationType as _RelationType


class PackageRelation(Base):
    __tablename__ = "PackageRelations"

    PackageID = Column(
        Integer, ForeignKey("Packages.ID", ondelete="CASCADE"),
        nullable=False)
    Package = relationship(
        _Package, backref=backref("package_relations", lazy="dynamic",
                                  cascade="all, delete"),
        foreign_keys=[PackageID])

    RelTypeID = Column(
        Integer, ForeignKey("RelationTypes.ID", ondelete="CASCADE"),
        nullable=False)
    RelationType = relationship(
        _RelationType, backref=backref("package_relations", lazy="dynamic"),
        foreign_keys=[RelTypeID])

    RelName = Column(String(255), unique=True)

    __mapper_args__ = {"primary_key": [PackageID, RelName]}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if not self.Package and not self.PackageID:
            raise IntegrityError(
                statement="Foreign key PackageID cannot be null.",
                orig="PackageRelations.PackageID",
                params=("NULL"))

        if not self.RelationType and not self.RelTypeID:
            raise IntegrityError(
                statement="Foreign key RelTypeID cannot be null.",
                orig="PackageRelations.RelTypeID",
                params=("NULL"))

        if not self.RelName:
            raise IntegrityError(
                statement="Column RelName cannot be null.",
                orig="PackageRelations.RelName",
                params=("NULL"))
