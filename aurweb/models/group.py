from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import mapper

from aurweb.schema import Groups


class Group:
    def __init__(self, Name: str = None):
        self.Name = Name
        if not self.Name:
            raise IntegrityError(
                statement="Column Name cannot be null.",
                orig="Groups.Name",
                params=("NULL"))


mapper(Group, Groups)
