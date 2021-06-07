from sqlalchemy import Column, String
from sqlalchemy.exc import IntegrityError

from aurweb.models.declarative import Base


class ApiRateLimit(Base):
    __tablename__ = "ApiRateLimit"

    IP = Column(String(45), primary_key=True, unique=True, default=str())

    __mapper_args__ = {"primary_key": [IP]}

    def __init__(self,
                 IP: str = None,
                 Requests: int = None,
                 WindowStart: int = None):
        self.IP = IP

        self.Requests = Requests
        if self.Requests is None:
            raise IntegrityError(
                statement="Column Requests cannot be null.",
                orig="ApiRateLimit.Requests",
                params=("NULL"))

        self.WindowStart = WindowStart
        if self.WindowStart is None:
            raise IntegrityError(
                statement="Column WindowStart cannot be null.",
                orig="ApiRateLimit.WindowStart",
                params=("NULL"))
