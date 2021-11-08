from sqlalchemy.exc import IntegrityError

from aurweb import schema
from aurweb.models.declarative import Base


class Term(Base):
    __table__ = schema.Terms
    __tablename__ = __table__.name
    __mapper_args__ = {"primary_key": [__table__.c.ID]}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if not self.Description:
            raise IntegrityError(
                statement="Column Description cannot be null.",
                orig="Terms.Description",
                params=("NULL"))

        if not self.URL:
            raise IntegrityError(
                statement="Column URL cannot be null.",
                orig="Terms.URL",
                params=("NULL"))
