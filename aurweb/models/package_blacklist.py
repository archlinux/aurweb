from sqlalchemy.exc import IntegrityError

from aurweb import schema
from aurweb.models.declarative import Base


class PackageBlacklist(Base):
    __table__ = schema.PackageBlacklist
    __tablename__ = __table__.name
    __mapper_args__ = {"primary_key": [__table__.c.ID]}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if not self.Name:
            raise IntegrityError(
                statement="Column Name cannot be null.",
                orig="PackageBlacklist.Name",
                params=("NULL"),
            )
