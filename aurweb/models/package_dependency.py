from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import backref, relationship

from aurweb import schema
from aurweb.models.declarative import Base
from aurweb.models.dependency_type import DependencyType as _DependencyType
from aurweb.models.package import Package as _Package


class PackageDependency(Base):
    __table__ = schema.PackageDepends
    __tablename__ = __table__.name
    __mapper_args__ = {
        "primary_key": [__table__.c.PackageID, __table__.c.DepName]
    }

    Package = relationship(
        _Package, backref=backref("package_dependencies", lazy="dynamic",
                                  cascade="all, delete"),
        foreign_keys=[__table__.c.PackageID])

    DependencyType = relationship(
        _DependencyType,
        backref=backref("package_dependencies", lazy="dynamic"),
        foreign_keys=[__table__.c.DepTypeID])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if not self.Package and not self.PackageID:
            raise IntegrityError(
                statement="Foreign key PackageID cannot be null.",
                orig="PackageDependencies.PackageID",
                params=("NULL"))

        if not self.DependencyType and not self.DepTypeID:
            raise IntegrityError(
                statement="Foreign key DepTypeID cannot be null.",
                orig="PackageDependencies.DepTypeID",
                params=("NULL"))

        if self.DepName is None:
            raise IntegrityError(
                statement="Column DepName cannot be null.",
                orig="PackageDependencies.DepName",
                params=("NULL"))

    def is_package(self) -> bool:
        # TODO: Improve the speed of this query if possible.
        from aurweb import db
        from aurweb.models.official_provider import OfficialProvider
        from aurweb.models.package import Package
        pkg = db.query(Package, Package.Name == self.DepName)
        official = db.query(OfficialProvider,
                            OfficialProvider.Name == self.DepName)
        return pkg.scalar() or official.scalar()
