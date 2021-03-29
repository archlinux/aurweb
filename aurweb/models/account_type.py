from sqlalchemy.orm import mapper

from aurweb.schema import AccountTypes


class AccountType:
    """ An ORM model of a single AccountTypes record. """

    def __init__(self, **kwargs):
        self.AccountType = kwargs.pop("AccountType")

    def __str__(self):
        return str(self.AccountType)

    def __repr__(self):
        return "<AccountType(ID='%s', AccountType='%s')>" % (
            self.ID, str(self))


mapper(AccountType, AccountTypes, confirm_deleted_rows=False)
