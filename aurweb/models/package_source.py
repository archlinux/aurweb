from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import backref, relationship

from aurweb import schema
from aurweb.models.declarative import Base
from aurweb.models.package import Package as _Package


class PackageSource(Base):
    __table__ = schema.PackageSources
    __tablename__ = __table__.name
    __mapper_args__ = {"primary_key": [__table__.c.PackageID, __table__.c.Source]}

    Package = relationship(
        _Package,
        backref=backref("package_sources", lazy="dynamic", cascade="all, delete"),
        foreign_keys=[__table__.c.PackageID],
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if not self.Package and not self.PackageID:
            raise IntegrityError(
                statement="Foreign key PackageID cannot be null.",
                orig="PackageSources.PackageID",
                params=("NULL"),
            )

        if not self.Source:
            self.Source = "/dev/null"
