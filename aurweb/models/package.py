from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import backref, relationship

from aurweb import schema
from aurweb.models.declarative import Base
from aurweb.models.package_base import PackageBase as _PackageBase


class Package(Base):
    __table__ = schema.Packages
    __tablename__ = __table__.name
    __mapper_args__ = {"primary_key": [__table__.c.ID]}

    PackageBase = relationship(
        _PackageBase, backref=backref("packages", lazy="dynamic"),
        foreign_keys=[__table__.c.PackageBaseID])

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
