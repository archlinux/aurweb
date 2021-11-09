from sqlalchemy.exc import IntegrityError

from aurweb import schema
from aurweb.models.declarative import Base

OFFICIAL_BASE = "https://archlinux.org"


class OfficialProvider(Base):
    __table__ = schema.OfficialProviders
    __tablename__ = __table__.name
    __mapper_args__ = {"primary_key": [__table__.c.ID]}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if not self.Name:
            raise IntegrityError(
                statement="Column Name cannot be null.",
                orig="OfficialProviders.Name",
                params=("NULL"))

        if not self.Repo:
            raise IntegrityError(
                statement="Column Repo cannot be null.",
                orig="OfficialProviders.Repo",
                params=("NULL"))

        if not self.Provides:
            raise IntegrityError(
                statement="Column Provides cannot be null.",
                orig="OfficialProviders.Provides",
                params=("NULL"))
