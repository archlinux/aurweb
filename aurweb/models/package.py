from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import backref, relationship

from aurweb.models.declarative import Base
from aurweb.models.package_base import PackageBase as _PackageBase


class Package(Base):
    __tablename__ = "Packages"

    ID = Column(Integer, primary_key=True)

    PackageBaseID = Column(
        Integer, ForeignKey("PackageBases.ID", ondelete="CASCADE"),
        nullable=False)
    PackageBase = relationship(
        _PackageBase, backref=backref("packages", lazy="dynamic"),
        foreign_keys=[PackageBaseID])

    __mapper_args__ = {"primary_key": [ID]}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if not self.PackageBase and not self.PackageBaseID:
            raise IntegrityError(
                statement="Foreign key PackageBaseID cannot be null.",
                orig="Packages.PackageBaseID",
                params=("NULL"))

        if self.Name is None:
            raise IntegrityError(
                statement="Column Name cannot be null.",
                orig="Packages.Name",
                params=("NULL"))
