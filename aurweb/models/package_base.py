from datetime import datetime

from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import backref, relationship

import aurweb.models.user

from aurweb.models.declarative import Base


class PackageBase(Base):
    __tablename__ = "PackageBases"

    FlaggerUID = Column(Integer,
                        ForeignKey("Users.ID", ondelete="SET NULL"))
    Flagger = relationship(
        "User", backref=backref("flagged_bases", lazy="dynamic"),
        foreign_keys=[FlaggerUID])

    SubmitterUID = Column(Integer,
                          ForeignKey("Users.ID", ondelete="SET NULL"))
    Submitter = relationship(
        "User", backref=backref("submitted_bases", lazy="dynamic"),
        foreign_keys=[SubmitterUID])

    MaintainerUID = Column(Integer,
                           ForeignKey("Users.ID", ondelete="SET NULL"))
    Maintainer = relationship(
        "User", backref=backref("maintained_bases", lazy="dynamic"),
        foreign_keys=[MaintainerUID])

    PackagerUID = Column(Integer, ForeignKey("Users.ID", ondelete="SET NULL"))
    Packager = relationship(
        "User", backref=backref("package_bases", lazy="dynamic"),
        foreign_keys=[PackagerUID])

    # A set used to check for floatable values.
    TO_FLOAT = {"Popularity"}

    def __init__(self, Name: str = None,
                 Flagger: aurweb.models.user.User = None,
                 Maintainer: aurweb.models.user.User = None,
                 Submitter: aurweb.models.user.User = None,
                 Packager: aurweb.models.user.User = None,
                 **kwargs):
        super().__init__(**kwargs)
        self.Name = Name
        if not self.Name:
            raise IntegrityError(
                statement="Column Name cannot be null.",
                orig="PackageBases.Name",
                params=("NULL"))

        self.Flagger = Flagger
        self.Maintainer = Maintainer
        self.Submitter = Submitter
        self.Packager = Packager

        self.NumVotes = kwargs.get("NumVotes")
        self.Popularity = kwargs.get("Popularity")
        self.OutOfDateTS = kwargs.get("OutOfDateTS")
        self.FlaggerComment = kwargs.get("FlaggerComment", str())
        self.SubmittedTS = kwargs.get("SubmittedTS",
                                      datetime.utcnow().timestamp())
        self.ModifiedTS = kwargs.get("ModifiedTS",
                                     datetime.utcnow().timestamp())

    def __getattribute__(self, key: str):
        attr = super().__getattribute__(key)
        if key in PackageBase.TO_FLOAT and not isinstance(attr, float):
            return float(attr)
        return attr
