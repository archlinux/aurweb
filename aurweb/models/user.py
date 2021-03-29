from sqlalchemy.orm import backref, mapper, relationship

from aurweb.models.account_type import AccountType
from aurweb.schema import Users


class User:
    """ An ORM model of a single Users record. """

    def __init__(self, **kwargs):
        self.AccountTypeID = kwargs.get("AccountTypeID")

        account_type = kwargs.get("AccountType")
        if account_type:
            self.AccountType = account_type

        self.Username = kwargs.get("Username")
        self.Email = kwargs.get("Email")
        self.BackupEmail = kwargs.get("BackupEmail")
        self.Passwd = kwargs.get("Passwd")
        self.Salt = kwargs.get("Salt")
        self.RealName = kwargs.get("RealName")
        self.LangPreference = kwargs.get("LangPreference")
        self.Timezone = kwargs.get("Timezone")
        self.Homepage = kwargs.get("Homepage")
        self.IRCNick = kwargs.get("IRCNick")
        self.PGPKey = kwargs.get("PGPKey")
        self.RegistrationTS = kwargs.get("RegistrationTS")
        self.CommentNotify = kwargs.get("CommentNotify")
        self.UpdateNotify = kwargs.get("UpdateNotify")
        self.OwnershipNotify = kwargs.get("OwnershipNotify")
        self.SSOAccountID = kwargs.get("SSOAccountID")

    def __repr__(self):
        return "<User(ID='%s', AccountType='%s', Username='%s')>" % (
            self.ID, str(self.AccountType), self.Username)


# Map schema.Users to User and give it some relationships.
mapper(User, Users, properties={
    "AccountType": relationship(AccountType,
                                backref=backref("users", lazy="dynamic"))
})
