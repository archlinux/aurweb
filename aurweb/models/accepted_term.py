from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import backref, relationship

import aurweb.models.term
import aurweb.models.user

from aurweb.models.declarative import Base


class AcceptedTerm(Base):
    __tablename__ = "AcceptedTerms"

    UsersID = Column(Integer, ForeignKey("Users.ID", ondelete="CASCADE"),
                     nullable=False)
    User = relationship(
        "User", backref=backref("accepted_terms", lazy="dynamic"),
        foreign_keys=[UsersID])

    TermsID = Column(Integer, ForeignKey("Terms.ID", ondelete="CASCADE"),
                     nullable=False)
    Term = relationship(
        "Term", backref=backref("accepted_terms", lazy="dynamic"),
        foreign_keys=[TermsID])

    __mapper_args__ = {"primary_key": [TermsID]}

    def __init__(self,
                 User: aurweb.models.user.User = None,
                 Term: aurweb.models.term.Term = None,
                 Revision: int = None):
        self.User = User
        if not self.User:
            raise IntegrityError(
                statement="Foreign key UserID cannot be null.",
                orig="AcceptedTerms.UserID",
                params=("NULL"))

        self.Term = Term
        if not self.Term:
            raise IntegrityError(
                statement="Foreign key TermID cannot be null.",
                orig="AcceptedTerms.TermID",
                params=("NULL"))

        self.Revision = Revision
