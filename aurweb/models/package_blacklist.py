from sqlalchemy import Column, Integer
from sqlalchemy.exc import IntegrityError

from aurweb.models.declarative import Base


class PackageBlacklist(Base):
    __tablename__ = "PackageBlacklist"

    ID = Column(Integer, primary_key=True)

    __mapper_args__ = {"primary_key": [ID]}

    def __init__(self, Name: str = None):
        self.Name = Name
        if not self.Name:
            raise IntegrityError(
                statement="Column Name cannot be null.",
                orig="PackageBlacklist.Name",
                params=("NULL"))
