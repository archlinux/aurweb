from sqlalchemy.orm import mapper

from aurweb.schema import DependencyTypes


class DependencyType:
    def __init__(self, Name: str = None):
        self.Name = Name


mapper(DependencyType, DependencyTypes)
