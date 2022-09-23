from typing import Any

from fastapi import Request

from aurweb import cookies, db, models, time, util
from aurweb.models import SSHPubKey
from aurweb.models.ssh_pub_key import get_fingerprint
from aurweb.util import strtobool


@db.retry_deadlock
def simple(
    U: str = str(),
    E: str = str(),
    H: bool = False,
    BE: str = str(),
    R: str = str(),
    HP: str = str(),
    I: str = str(),
    K: str = str(),
    J: bool = False,
    CN: bool = False,
    UN: bool = False,
    ON: bool = False,
    S: bool = False,
    user: models.User = None,
    **kwargs,
) -> None:
    now = time.utcnow()
    with db.begin():
        user.Username = U or user.Username
        user.Email = E or user.Email
        user.HideEmail = strtobool(H)
        user.BackupEmail = user.BackupEmail if BE is None else BE
        user.RealName = user.RealName if R is None else R
        user.Homepage = user.Homepage if HP is None else HP
        user.IRCNick = user.IRCNick if I is None else I
        user.PGPKey = user.PGPKey if K is None else K
        user.Suspended = strtobool(S)
        user.InactivityTS = now * int(strtobool(J))
        user.CommentNotify = strtobool(CN)
        user.UpdateNotify = strtobool(UN)
        user.OwnershipNotify = strtobool(ON)


@db.retry_deadlock
def language(
    L: str = str(),
    request: Request = None,
    user: models.User = None,
    context: dict[str, Any] = {},
    **kwargs,
) -> None:
    if L and L != user.LangPreference:
        with db.begin():
            user.LangPreference = L
        context["language"] = L


@db.retry_deadlock
def timezone(
    TZ: str = str(),
    request: Request = None,
    user: models.User = None,
    context: dict[str, Any] = {},
    **kwargs,
) -> None:
    if TZ and TZ != user.Timezone:
        with db.begin():
            user.Timezone = TZ
        context["language"] = TZ


@db.retry_deadlock
def ssh_pubkey(PK: str = str(), user: models.User = None, **kwargs) -> None:
    if not PK:
        # If no pubkey is provided, wipe out any pubkeys the user
        # has and return out early.
        with db.begin():
            db.delete_all(user.ssh_pub_keys)
        return

    # Otherwise, parse ssh keys and their fprints out of PK.
    keys = util.parse_ssh_keys(PK.strip())
    fprints = [get_fingerprint(" ".join(k)) for k in keys]

    with db.begin():
        # Delete any existing keys we can't find.
        to_remove = user.ssh_pub_keys.filter(~SSHPubKey.Fingerprint.in_(fprints))
        db.delete_all(to_remove)

        # For each key, if it does not yet exist, create it.
        for i, full_key in enumerate(keys):
            prefix, key = full_key
            exists = user.ssh_pub_keys.filter(
                SSHPubKey.Fingerprint == fprints[i]
            ).exists()
            if not db.query(exists).scalar():
                # No public key exists, create one.
                db.create(
                    models.SSHPubKey,
                    UserID=user.ID,
                    PubKey=" ".join([prefix, key]),
                    Fingerprint=fprints[i],
                )


@db.retry_deadlock
def account_type(T: int = None, user: models.User = None, **kwargs) -> None:
    if T is not None and (T := int(T)) != user.AccountTypeID:
        with db.begin():
            user.AccountTypeID = T


@db.retry_deadlock
def password(
    P: str = str(),
    request: Request = None,
    user: models.User = None,
    context: dict[str, Any] = {},
    **kwargs,
) -> None:
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


@db.retry_deadlock
def suspend(
    S: bool = False,
    request: Request = None,
    user: models.User = None,
    context: dict[str, Any] = {},
    **kwargs,
) -> None:
    if S and user.session:
        context["S"] = None
        with db.begin():
            db.delete_all(
                db.query(models.Session).filter(models.Session.UsersID == user.ID)
            )
