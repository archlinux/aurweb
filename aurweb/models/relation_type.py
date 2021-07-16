from sqlalchemy import Column, Integer

from aurweb import db
from aurweb.models.declarative import Base

CONFLICTS = "conflicts"
PROVIDES = "provides"
REPLACES = "replaces"


class RelationType(Base):
    __tablename__ = "RelationTypes"

    ID = Column(Integer, primary_key=True)

    __mapper_args__ = {"primary_key": [ID]}

    def __init__(self, Name: str = None):
        self.Name = Name


CONFLICTS_ID = db.query(RelationType).filter(
    RelationType.Name == CONFLICTS).first().ID
PROVIDES_ID = db.query(RelationType).filter(
    RelationType.Name == PROVIDES).first().ID
REPLACES_ID = db.query(RelationType).filter(
    RelationType.Name == REPLACES).first().ID
