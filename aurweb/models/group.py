from sqlalchemy import Column, Integer
from sqlalchemy.exc import IntegrityError

from aurweb.models.declarative import Base


class Group(Base):
    __tablename__ = "Groups"

    ID = Column(Integer, primary_key=True)

    __mapper_args__ = {"primary_key": [ID]}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.Name is None:
            raise IntegrityError(
                statement="Column Name cannot be null.",
                orig="Groups.Name",
                params=("NULL"))
