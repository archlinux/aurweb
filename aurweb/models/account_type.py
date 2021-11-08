from aurweb import schema
from aurweb.models.declarative import Base

USER = "User"
TRUSTED_USER = "Trusted User"
DEVELOPER = "Developer"
TRUSTED_USER_AND_DEV = "Trusted User & Developer"

USER_ID = 1
TRUSTED_USER_ID = 2
DEVELOPER_ID = 3
TRUSTED_USER_AND_DEV_ID = 4

# Map string constants to integer constants.
ACCOUNT_TYPE_ID = {
    USER: USER_ID,
    TRUSTED_USER: TRUSTED_USER_ID,
    DEVELOPER: DEVELOPER_ID,
    TRUSTED_USER_AND_DEV: TRUSTED_USER_AND_DEV_ID
}

# Reversed ACCOUNT_TYPE_ID mapping.
ACCOUNT_TYPE_NAME = {v: k for k, v in ACCOUNT_TYPE_ID.items()}


class AccountType(Base):
    """ An ORM model of a single AccountTypes record. """
    __table__ = schema.AccountTypes
    __tablename__ = __table__.name
    __mapper_args__ = {"primary_key": [__table__.c.ID]}

    def __init__(self, **kwargs):
        self.AccountType = kwargs.pop("AccountType")

    def __str__(self):
        return str(self.AccountType)

    def __repr__(self):
        return "<AccountType(ID='%s', AccountType='%s')>" % (
            self.ID, str(self))
