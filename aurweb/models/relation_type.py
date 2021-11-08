from aurweb import schema
from aurweb.models.declarative import Base

CONFLICTS = "conflicts"
PROVIDES = "provides"
REPLACES = "replaces"

CONFLICTS_ID = 1
PROVIDES_ID = 2
REPLACES_ID = 3


class RelationType(Base):
    __table__ = schema.RelationTypes
    __tablename__ = __table__.name
    __mapper_args__ = {"primary_key": [__table__.c.ID]}

    def __init__(self, Name: str = None):
        self.Name = Name
