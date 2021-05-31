from sqlalchemy.orm import mapper

from aurweb.db import make_relationship
from aurweb.models.term import Term
from aurweb.models.user import User
from aurweb.schema import AcceptedTerms


class AcceptedTerm:
    def __init__(self,
                 User: User = None, Term: Term = None,
                 Revision: int = None):
        self.User = User
        self.Term = Term
        self.Revision = Revision


properties = {
    "User": make_relationship(User, AcceptedTerms.c.UsersID, "accepted_terms"),
    "Term": make_relationship(Term, AcceptedTerms.c.TermsID, "accepted")
}

mapper(AcceptedTerm, AcceptedTerms, properties=properties,
       primary_key=[AcceptedTerms.c.UsersID, AcceptedTerms.c.TermsID])
