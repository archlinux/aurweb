from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import backref, relationship

from aurweb import schema
from aurweb.models.declarative import Base
from aurweb.models.package_base import PackageBase as _PackageBase


class PackageKeyword(Base):
    __table__ = schema.PackageKeywords
    __tablename__ = __table__.name
    __mapper_args__ = {"primary_key": [__table__.c.PackageBaseID, __table__.c.Keyword]}

    PackageBase = relationship(
        _PackageBase,
        backref=backref("keywords", lazy="dynamic", cascade="all, delete"),
        foreign_keys=[__table__.c.PackageBaseID],
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if not self.PackageBase and not self.PackageBaseID:
            raise IntegrityError(
                statement="Primary key PackageBaseID cannot be null.",
                orig="PackageKeywords.PackageBaseID",
                params=("NULL"),
            )
