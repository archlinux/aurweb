from sqlalchemy.exc import IntegrityError

from aurweb import schema
from aurweb.models.declarative import Base


class ApiRateLimit(Base):
    __table__ = schema.ApiRateLimit
    __tablename__ = __table__.name
    __mapper_args__ = {"primary_key": [__table__.c.IP]}

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
