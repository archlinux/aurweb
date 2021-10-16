from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import backref, relationship

from aurweb.models.declarative import Base
from aurweb.models.package import Package as _Package


class PackageSource(Base):
    __tablename__ = "PackageSources"

    PackageID = Column(Integer, ForeignKey("Packages.ID", ondelete="CASCADE"),
                       nullable=False)
    Package = relationship(
        _Package, backref=backref("package_sources", lazy="dynamic",
                                  cascade="all, delete"),
        foreign_keys=[PackageID])

    __mapper_args__ = {"primary_key": [PackageID]}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if not self.Package and not self.PackageID:
            raise IntegrityError(
                statement="Foreign key PackageID cannot be null.",
                orig="PackageSources.PackageID",
                params=("NULL"))
