from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import backref, relationship

from aurweb import schema
from aurweb.models.declarative import Base
from aurweb.models.term import Term as _Term
from aurweb.models.user import User as _User


class AcceptedTerm(Base):
    __table__ = schema.AcceptedTerms
    __tablename__ = __table__.name
    __mapper_args__ = {"primary_key": [__table__.c.TermsID]}

    User = relationship(
        _User, backref=backref("accepted_terms", lazy="dynamic"),
        foreign_keys=[__table__.c.UsersID])

    Term = relationship(
        _Term, backref=backref("accepted_terms", lazy="dynamic"),
        foreign_keys=[__table__.c.TermsID])

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
