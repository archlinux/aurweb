from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import backref, relationship

from aurweb import schema
from aurweb.models.declarative import Base
from aurweb.models.package import Package as _Package
from aurweb.models.relation_type import RelationType as _RelationType


class PackageRelation(Base):
    __table__ = schema.PackageRelations
    __tablename__ = __table__.name
    __mapper_args__ = {
        "primary_key": [__table__.c.PackageID, __table__.c.RelName]
    }

    Package = relationship(
        _Package, backref=backref("package_relations", lazy="dynamic",
                                  cascade="all, delete"),
        foreign_keys=[__table__.c.PackageID])

    RelationType = relationship(
        _RelationType, backref=backref("package_relations", lazy="dynamic"),
        foreign_keys=[__table__.c.RelTypeID])

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
