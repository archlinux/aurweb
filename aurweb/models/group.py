from sqlalchemy.orm import mapper

from aurweb.schema import Groups


class Group:
    def __init__(self, Name: str = None):
        self.Name = Name


mapper(Group, Groups)
