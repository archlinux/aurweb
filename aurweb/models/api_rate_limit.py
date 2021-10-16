from sqlalchemy import Column, String
from sqlalchemy.exc import IntegrityError

from aurweb.models.declarative import Base


class ApiRateLimit(Base):
    __tablename__ = "ApiRateLimit"

    IP = Column(String(45), primary_key=True, unique=True, default=str())

    __mapper_args__ = {"primary_key": [IP]}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if self.Requests is None:
            raise IntegrityError(
                statement="Column Requests cannot be null.",
                orig="ApiRateLimit.Requests",
                params=("NULL"))

        if self.WindowStart is None:
            raise IntegrityError(
                statement="Column WindowStart cannot be null.",
                orig="ApiRateLimit.WindowStart",
                params=("NULL"))
