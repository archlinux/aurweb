from sqlalchemy import Column, ForeignKey, Integer, String, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import backref, relationship

import aurweb.db
import aurweb.models.package_base

from aurweb.models.declarative import Base


class PackageKeyword(Base):
    __tablename__ = "PackageKeywords"

    PackageBaseID = Column(
        Integer, ForeignKey("PackageBases.ID", ondelete="CASCADE"),
        primary_key=True, nullable=True)
    PackageBase = relationship(
        "PackageBase", backref=backref("keywords", lazy="dynamic"),
        foreign_keys=[PackageBaseID])

    Keyword = Column(
        String(255), primary_key=True, nullable=False,
        server_default=text("''"))

    __mapper_args__ = {"primary_key": [PackageBaseID, Keyword]}

    def __init__(self,
                 PackageBase: aurweb.models.package_base.PackageBase = None,
                 Keyword: str = None):
        self.PackageBase = PackageBase
        if not self.PackageBase:
            raise IntegrityError(
                statement="Primary key PackageBaseID cannot be null.",
                orig="PackageKeywords.PackageBaseID",
                params=("NULL"))

        self.Keyword = Keyword
