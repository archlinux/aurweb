from sqlalchemy import Column, ForeignKey, Integer, String, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import backref, relationship

from aurweb.models.declarative import Base
from aurweb.models.package_base import PackageBase as _PackageBase


class PackageKeyword(Base):
    __tablename__ = "PackageKeywords"

    PackageBaseID = Column(
        Integer, ForeignKey("PackageBases.ID", ondelete="CASCADE"),
        primary_key=True, nullable=True)
    PackageBase = relationship(
        _PackageBase, backref=backref("keywords", lazy="dynamic",
                                      cascade="all, delete"),
        foreign_keys=[PackageBaseID])

    Keyword = Column(
        String(255), primary_key=True, nullable=False,
        server_default=text("''"))

    __mapper_args__ = {"primary_key": [PackageBaseID, Keyword]}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if not self.PackageBase and not self.PackageBaseID:
            raise IntegrityError(
                statement="Primary key PackageBaseID cannot be null.",
                orig="PackageKeywords.PackageBaseID",
                params=("NULL"))
