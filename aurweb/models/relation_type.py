from sqlalchemy import Column, Integer

from aurweb.models.declarative import Base


class RelationType(Base):
    __tablename__ = "RelationTypes"

    ID = Column(Integer, primary_key=True)

    __mapper_args__ = {"primary_key": [ID]}

    def __init__(self, Name: str = None):
        self.Name = Name