from sqlalchemy import Column, Integer
from sqlalchemy.exc import IntegrityError

from aurweb.models.declarative import Base


class Term(Base):
    __tablename__ = "Terms"

    ID = Column(Integer, primary_key=True)

    __mapper_args__ = {"primary_key": [ID]}

    def __init__(self,
                 Description: str = None, URL: str = None,
                 Revision: int = None):
        self.Description = Description
        if not self.Description:
            raise IntegrityError(
                statement="Column Description cannot be null.",
                orig="Terms.Description",
                params=("NULL"))

        self.URL = URL
        if not self.URL:
            raise IntegrityError(
                statement="Column URL cannot be null.",
                orig="Terms.URL",
                params=("NULL"))

        self.Revision = Revision
