from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import backref, relationship

import aurweb.models.package

from aurweb.models import dependency_type
from aurweb.models.declarative import Base


class PackageDependency(Base):
    __tablename__ = "PackageDepends"

    PackageID = Column(
        Integer, ForeignKey("Packages.ID", ondelete="CASCADE"),
        nullable=False)
    Package = relationship(
        "Package", backref=backref("package_dependencies", lazy="dynamic"),
        foreign_keys=[PackageID])

    DepTypeID = Column(
        Integer, ForeignKey("DependencyTypes.ID", ondelete="NO ACTION"),
        nullable=False)
    DependencyType = relationship(
        "DependencyType",
        backref=backref("package_dependencies", lazy="dynamic"),
        foreign_keys=[DepTypeID])

    DepName = Column(String(255), nullable=False)

    __mapper_args__ = {"primary_key": [PackageID, DepName]}

    def __init__(self,
                 Package: aurweb.models.package.Package = None,
                 DependencyType: dependency_type.DependencyType = None,
                 DepName: str = None,
                 DepDesc: str = None,
                 DepCondition: str = None,
                 DepArch: str = None):
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
