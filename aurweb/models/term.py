from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import mapper

from aurweb.schema import Terms


class Term:
    def __init__(self,
                 Description: str = None, URL: str = None,
                 Revision: int = None):
        self.Description = Description
        if not self.Description:
            raise IntegrityError(
                statement="Column Description cannot be null.",
                orig="Terms.Description",
                params=("NULL"))

        self.URL = URL
        if not self.URL:
            raise IntegrityError(
                statement="Column URL cannot be null.",
                orig="Terms.URL",
                params=("NULL"))

        self.Revision = Revision


mapper(Term, Terms)
