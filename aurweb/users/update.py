from datetime import datetime
from typing import Any, Dict

from fastapi import Request

from aurweb import cookies, db, models
from aurweb.models.ssh_pub_key import get_fingerprint
from aurweb.util import strtobool


def simple(U: str = str(), E: str = str(), H: bool = False,
           BE: str = str(), R: str = str(), HP: str = str(),
           I: str = str(), K: str = str(), J: bool = False,
           CN: bool = False, UN: bool = False, ON: bool = False,
           S: bool = False, user: models.User = None,
           **kwargs) -> None:
    now = int(datetime.utcnow().timestamp())
    with db.begin():
        user.Username = U or user.Username
        user.Email = E or user.Email
        user.HideEmail = strtobool(H)
        user.BackupEmail = BE or user.BackupEmail
        user.RealName = R or user.RealName
        user.Homepage = HP or user.Homepage
        user.IRCNick = I or user.IRCNick
        user.PGPKey = K or user.PGPKey
        user.Suspended = strtobool(S)
        user.InactivityTS = now * int(strtobool(J))
        user.CommentNotify = strtobool(CN)
        user.UpdateNotify = strtobool(UN)
        user.OwnershipNotify = strtobool(ON)


def language(L: str = str(),
             request: Request = None,
             user: models.User = None,
             context: Dict[str, Any] = {},
             **kwargs) -> None:
    if L and L != user.LangPreference:
        with db.begin():
            user.LangPreference = L
        context["language"] = L


def timezone(TZ: str = str(),
             request: Request = None,
             user: models.User = None,
             context: Dict[str, Any] = {},
             **kwargs) -> None:
    if TZ and TZ != user.Timezone:
        with db.begin():
            user.Timezone = TZ
        context["language"] = TZ


def ssh_pubkey(PK: str = str(),
               user: models.User = None,
               **kwargs) -> None:
    # If a PK is given, compare it against the target user's PK.
    if PK:
        # Get the second token in the public key, which is the actual key.
        pubkey = PK.strip().rstrip()
        parts = pubkey.split(" ")
        if len(parts) == 3:
            # Remove the host part.
            pubkey = parts[0] + " " + parts[1]
        fingerprint = get_fingerprint(pubkey)
        if not user.ssh_pub_key:
            # No public key exists, create one.
            with db.begin():
                db.create(models.SSHPubKey, UserID=user.ID,
                          PubKey=pubkey, Fingerprint=fingerprint)
        elif user.ssh_pub_key.PubKey != pubkey:
            # A public key already exists, update it.
            with db.begin():
                user.ssh_pub_key.PubKey = pubkey
                user.ssh_pub_key.Fingerprint = fingerprint
    elif user.ssh_pub_key:
        # Else, if the user has a public key already, delete it.
        with db.begin():
            db.delete(user.ssh_pub_key)


def account_type(T: int = None,
                 user: models.User = None,
                 **kwargs) -> None:
    if T is not None and (T := int(T)) != user.AccountTypeID:
        with db.begin():
            user.AccountTypeID = T


def password(P: str = str(),
             request: Request = None,
             user: models.User = None,
             context: Dict[str, Any] = {},
             **kwargs) -> None:
    if P and not user.valid_password(P):
        # Remove the fields we consumed for passwords.
        context["P"] = context["C"] = str()

        # If a password was given and it doesn't match the user's, update it.
        with db.begin():
            user.update_password(P)

        if user == request.user:
            remember_me = request.cookies.get("AURREMEMBER", False)

            # If the target user is the request user, login with
            # the updated password to update the Session record.
            user.login(request, P, cookies.timeout(remember_me))
