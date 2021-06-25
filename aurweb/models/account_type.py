from sqlalchemy import Column, Integer

from aurweb import db
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


# Define some AccountType.AccountType constants.
USER = "User"
TRUSTED_USER = "Trusted User"
DEVELOPER = "Developer"
TRUSTED_USER_AND_DEV = "Trusted User & Developer"

# Fetch account type IDs from the database for constants.
_account_types = db.query(AccountType)
USER_ID = _account_types.filter(
    AccountType.AccountType == USER).first().ID
TRUSTED_USER_ID = _account_types.filter(
    AccountType.AccountType == TRUSTED_USER).first().ID
DEVELOPER_ID = _account_types.filter(
    AccountType.AccountType == DEVELOPER).first().ID
TRUSTED_USER_AND_DEV_ID = _account_types.filter(
    AccountType.AccountType == TRUSTED_USER_AND_DEV).first().ID
_account_types = None  # Get rid of the query handle.

# Map string constants to integer constants.
ACCOUNT_TYPE_ID = {
    USER: USER_ID,
    TRUSTED_USER: TRUSTED_USER_ID,
    DEVELOPER: DEVELOPER_ID,
    TRUSTED_USER_AND_DEV: TRUSTED_USER_AND_DEV_ID
}
