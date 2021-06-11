from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import backref, relationship

import aurweb.models.package

from aurweb.models.declarative import Base


class PackageSource(Base):
    __tablename__ = "PackageSources"

    PackageID = Column(Integer, ForeignKey("Packages.ID", ondelete="CASCADE"),
                       nullable=False)
    Package = relationship(
        "Package", backref=backref("package_sources", lazy="dynamic"),
        foreign_keys=[PackageID])

    __mapper_args__ = {"primary_key": [PackageID]}

    def __init__(self,
                 Package: aurweb.models.package.Package = None,
                 **kwargs):
        super().__init__(**kwargs)

        self.Package = Package
        if not self.Package:
            raise IntegrityError(
                statement="Foreign key PackageID cannot be null.",
                orig="PackageSources.PackageID",
                params=("NULL"))
