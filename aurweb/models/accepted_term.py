from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import backref, relationship

from aurweb.models.declarative import Base
from aurweb.models.term import Term as _Term
from aurweb.models.user import User as _User


class AcceptedTerm(Base):
    __tablename__ = "AcceptedTerms"

    UsersID = Column(Integer, ForeignKey("Users.ID", ondelete="CASCADE"),
                     nullable=False)
    User = relationship(
        _User, backref=backref("accepted_terms", lazy="dynamic"),
        foreign_keys=[UsersID])

    TermsID = Column(Integer, ForeignKey("Terms.ID", ondelete="CASCADE"),
                     nullable=False)
    Term = relationship(
        _Term, backref=backref("accepted_terms", lazy="dynamic"),
        foreign_keys=[TermsID])

    __mapper_args__ = {"primary_key": [TermsID]}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if not self.User and not self.UsersID:
            raise IntegrityError(
                statement="Foreign key UsersID cannot be null.",
                orig="AcceptedTerms.UserID",
                params=("NULL"))

        if not self.Term and not self.TermsID:
            raise IntegrityError(
                statement="Foreign key TermID cannot be null.",
                orig="AcceptedTerms.TermID",
                params=("NULL"))
