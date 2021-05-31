from sqlalchemy.orm import mapper

from aurweb.schema import Terms


class Term:
    def __init__(self,
                 Description: str = None, URL: str = None,
                 Revision: int = None):
        self.Description = Description
        self.URL = URL
        self.Revision = Revision


mapper(Term, Terms)
