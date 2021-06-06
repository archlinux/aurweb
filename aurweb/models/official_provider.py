from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import mapper

from aurweb.schema import OfficialProviders


class OfficialProvider:
    def __init__(self,
                 Name: str = None,
                 Repo: str = None,
                 Provides: str = None):
        self.Name = Name
        if not self.Name:
            raise IntegrityError(
                statement="Column Name cannot be null.",
                orig="OfficialProviders.Name",
                params=("NULL"))

        self.Repo = Repo
        if not self.Repo:
            raise IntegrityError(
                statement="Column Repo cannot be null.",
                orig="OfficialProviders.Repo",
                params=("NULL"))

        self.Provides = Provides
        if not self.Provides:
            raise IntegrityError(
                statement="Column Provides cannot be null.",
                orig="OfficialProviders.Provides",
                params=("NULL"))


mapper(OfficialProvider, OfficialProviders)
