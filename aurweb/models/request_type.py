from aurweb import schema
from aurweb.models.declarative import Base

DELETION = "deletion"
ORPHAN = "orphan"
MERGE = "merge"

DELETION_ID = 1
ORPHAN_ID = 2
MERGE_ID = 3


class RequestType(Base):
    __table__ = schema.RequestTypes
    __tablename__ = __table__.name
    __mapper_args__ = {"primary_key": [__table__.c.ID]}

    def name_display(self) -> str:
        """Return the Name column with its first char capitalized."""
        return self.Name.title()
