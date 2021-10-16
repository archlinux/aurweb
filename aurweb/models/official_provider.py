from sqlalchemy import Column, Integer
from sqlalchemy.exc import IntegrityError

from aurweb.models.declarative import Base

# TODO: Fix this! Official packages aren't from aur.archlinux.org...
OFFICIAL_BASE = "https://aur.archlinux.org"


class OfficialProvider(Base):
    __tablename__ = "OfficialProviders"

    ID = Column(Integer, primary_key=True)

    __mapper_args__ = {"primary_key": [ID]}

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
