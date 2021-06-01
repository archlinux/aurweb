from sqlalchemy.orm import mapper

from aurweb.schema import RelationTypes


class RelationType:
    def __init__(self, Name: str = None):
        self.Name = Name


mapper(RelationType, RelationTypes)
