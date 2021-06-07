from sqlalchemy import Column, Integer

from aurweb.models.declarative import Base


class AccountType(Base):
    """ An ORM model of a single AccountTypes record. """
    __tablename__ = "AccountTypes"

    ID = Column(Integer, primary_key=True)

    __mapper_args__ = {"primary_key": [ID]}

    def __init__(self, **kwargs):
        self.AccountType = kwargs.pop("AccountType")

    def __str__(self):
        return str(self.AccountType)

    def __repr__(self):
        return "<AccountType(ID='%s', AccountType='%s')>" % (
            self.ID, str(self))
