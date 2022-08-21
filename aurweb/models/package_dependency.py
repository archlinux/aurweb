from sqlalchemy import and_, literal
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import backref, relationship

from aurweb import db, schema
from aurweb.models.declarative import Base
from aurweb.models.dependency_type import DependencyType as _DependencyType
from aurweb.models.official_provider import OfficialProvider as _OfficialProvider
from aurweb.models.package import Package as _Package
from aurweb.models.package_relation import PackageRelation


class PackageDependency(Base):
    __table__ = schema.PackageDepends
    __tablename__ = __table__.name
    __mapper_args__ = {
        "primary_key": [
            __table__.c.PackageID,
            __table__.c.DepTypeID,
            __table__.c.DepName,
        ]
    }

    Package = relationship(
        _Package,
        backref=backref("package_dependencies", lazy="dynamic", cascade="all, delete"),
        foreign_keys=[__table__.c.PackageID],
    )

    DependencyType = relationship(
        _DependencyType,
        backref=backref("package_dependencies", lazy="dynamic"),
        foreign_keys=[__table__.c.DepTypeID],
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if not self.Package and not self.PackageID:
            raise IntegrityError(
                statement="Foreign key PackageID cannot be null.",
                orig="PackageDependencies.PackageID",
                params=("NULL"),
            )

        if not self.DependencyType and not self.DepTypeID:
            raise IntegrityError(
                statement="Foreign key DepTypeID cannot be null.",
                orig="PackageDependencies.DepTypeID",
                params=("NULL"),
            )

        if self.DepName is None:
            raise IntegrityError(
                statement="Column DepName cannot be null.",
                orig="PackageDependencies.DepName",
                params=("NULL"),
            )

    def is_package(self) -> bool:
        pkg = db.query(_Package).filter(_Package.Name == self.DepName).exists()
        official = (
            db.query(_OfficialProvider)
            .filter(_OfficialProvider.Name == self.DepName)
            .exists()
        )
        return db.query(pkg).scalar() or db.query(official).scalar()

    def provides(self) -> list[PackageRelation]:
        from aurweb.models.relation_type import PROVIDES_ID

        rels = (
            db.query(PackageRelation)
            .join(_Package)
            .filter(
                and_(
                    PackageRelation.RelTypeID == PROVIDES_ID,
                    PackageRelation.RelName == self.DepName,
                )
            )
            .with_entities(_Package.Name, literal(False).label("is_official"))
            .order_by(_Package.Name.asc())
        )

        official_rels = (
            db.query(_OfficialProvider)
            .filter(
                and_(
                    _OfficialProvider.Provides == self.DepName,
                    _OfficialProvider.Name != self.DepName,
                )
            )
            .with_entities(_OfficialProvider.Name, literal(True).label("is_official"))
            .order_by(_OfficialProvider.Name.asc())
        )

        return rels.union(official_rels).all()
