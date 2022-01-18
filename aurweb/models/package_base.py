from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import backref, relationship

from aurweb import schema, time
from aurweb.models.declarative import Base
from aurweb.models.user import User as _User


class PackageBase(Base):
    __table__ = schema.PackageBases
    __tablename__ = __table__.name
    __mapper_args__ = {"primary_key": [__table__.c.ID]}

    Flagger = relationship(
        _User, backref=backref("flagged_bases", lazy="dynamic"),
        foreign_keys=[__table__.c.FlaggerUID])

    Submitter = relationship(
        _User, backref=backref("submitted_bases", lazy="dynamic"),
        foreign_keys=[__table__.c.SubmitterUID])

    Maintainer = relationship(
        _User, backref=backref("maintained_bases", lazy="dynamic"),
        foreign_keys=[__table__.c.MaintainerUID])

    Packager = relationship(
        _User, backref=backref("package_bases", lazy="dynamic"),
        foreign_keys=[__table__.c.PackagerUID])

    # A set used to check for floatable values.
    TO_FLOAT = {"Popularity"}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if self.Name is None:
            raise IntegrityError(
                statement="Column Name cannot be null.",
                orig="PackageBases.Name",
                params=("NULL"))

        # If no SubmittedTS/ModifiedTS is provided on creation, set them
        # here to the current utc timestamp.
        now = time.utcnow()
        if not self.SubmittedTS:
            self.SubmittedTS = now
        if not self.ModifiedTS:
            self.ModifiedTS = now

        if not self.FlaggerComment:
            self.FlaggerComment = str()

    def __getattribute__(self, key: str):
        attr = super().__getattribute__(key)
        if key in PackageBase.TO_FLOAT and not isinstance(attr, float):
            return float(attr)
        return attr
