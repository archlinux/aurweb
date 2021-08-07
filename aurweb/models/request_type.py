from sqlalchemy import Column, Integer

from aurweb import db
from aurweb.models.declarative import Base

DELETION = "deletion"
ORPHAN = "orphan"
MERGE = "merge"


class RequestType(Base):
    __tablename__ = "RequestTypes"

    ID = Column(Integer, primary_key=True)

    __mapper_args__ = {"primary_key": [ID]}

    def name_display(self) -> str:
        """ Return the Name column with its first char capitalized. """
        name = self.Name
        return name[0].upper() + name[1:]


DELETION_ID = db.query(RequestType, RequestType.Name == DELETION).first().ID
ORPHAN_ID = db.query(RequestType, RequestType.Name == ORPHAN).first().ID
MERGE_ID = db.query(RequestType, RequestType.Name == MERGE).first().ID
