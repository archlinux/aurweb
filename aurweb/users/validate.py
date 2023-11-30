"""
Validation functions for account registration and edit fields.
Each of these functions extracts a subset of keyword arguments
out of form data from /account/register or /account/{username}/edit.

All functions in this module raise aurweb.exceptions.ValidationError
when encountering invalid criteria and return silently otherwise.
"""
from fastapi import Request
from sqlalchemy import and_, func

from aurweb import aur_logging, config, db, l10n, models, time, util
from aurweb.auth import creds
from aurweb.captcha import get_captcha_answer, get_captcha_salts, get_captcha_token
from aurweb.exceptions import ValidationError
from aurweb.models.account_type import ACCOUNT_TYPE_NAME
from aurweb.models.ssh_pub_key import get_fingerprint
from aurweb.util import strtobool

logger = aur_logging.get_logger(__name__)


def invalid_fields(E: str = str(), U: str = str(), **kwargs) -> None:
    if not E or not U:
        raise ValidationError(["Missing a required field."])


def invalid_suspend_permission(
    request: Request = None, user: models.User = None, S: str = "False", **kwargs
) -> None:
    if not request.user.is_elevated() and strtobool(S) != bool(user.Suspended):
        raise ValidationError(["You do not have permission to suspend accounts."])


def invalid_username(
    request: Request = None, U: str = str(), _: l10n.Translator = None, **kwargs
) -> None:
    if not util.valid_username(U):
        username_min_len = config.getint("options", "username_min_len")
        username_max_len = config.getint("options", "username_max_len")
        raise ValidationError(
            [
                "The username is invalid.",
                [
                    _("It must be between %s and %s characters long")
                    % (username_min_len, username_max_len),
                    "Start and end with a letter or number",
                    "Can contain only one period, underscore or hyphen.",
                ],
            ]
        )


def invalid_password(
    P: str = str(), C: str = str(), _: l10n.Translator = None, **kwargs
) -> None:
    if P:
        if not util.valid_password(P):
            passwd_min_len = config.getint("options", "passwd_min_len")
            raise ValidationError(
                [_("Your password must be at least %s characters.") % (passwd_min_len)]
            )
        elif not C:
            raise ValidationError(["Please confirm your new password."])
        elif P != C:
            raise ValidationError(["Password fields do not match."])


def is_banned(request: Request = None, **kwargs) -> None:
    host = util.get_client_ip(request)
    exists = db.query(models.Ban, models.Ban.IPAddress == host).exists()
    if db.query(exists).scalar():
        raise ValidationError(
            [
                "Account registration has been disabled for your "
                "IP address, probably due to sustained spam attacks. "
                "Sorry for the inconvenience."
            ]
        )


def invalid_user_password(
    request: Request = None, passwd: str = str(), **kwargs
) -> None:
    if request.user.is_authenticated():
        if not request.user.valid_password(passwd):
            raise ValidationError(["Invalid password."])


def invalid_email(E: str = str(), **kwargs) -> None:
    if not util.valid_email(E):
        raise ValidationError(["The email address is invalid."])


def invalid_backup_email(BE: str = str(), **kwargs) -> None:
    if BE and not util.valid_email(BE):
        raise ValidationError(["The backup email address is invalid."])


def invalid_homepage(HP: str = str(), **kwargs) -> None:
    if HP and not util.valid_homepage(HP):
        raise ValidationError(
            ["The home page is invalid, please specify the full HTTP(s) URL."]
        )


def invalid_pgp_key(K: str = str(), **kwargs) -> None:
    if K and not util.valid_pgp_fingerprint(K):
        raise ValidationError(["The PGP key fingerprint is invalid."])


def invalid_ssh_pubkey(
    PK: str = str(), user: models.User = None, _: l10n.Translator = None, **kwargs
) -> None:
    if not PK:
        return

    try:
        keys = util.parse_ssh_keys(PK.strip())
    except ValueError as exc:
        raise ValidationError([str(exc)])

    for prefix, key in keys:
        fingerprint = get_fingerprint(f"{prefix} {key}")

        exists = (
            db.query(models.SSHPubKey)
            .filter(
                and_(
                    models.SSHPubKey.UserID != user.ID,
                    models.SSHPubKey.Fingerprint == fingerprint,
                )
            )
            .exists()
        )
        if db.query(exists).scalar():
            raise ValidationError(
                [
                    _("The SSH public key, %s%s%s, is already in use.")
                    % ("<strong>", fingerprint, "</strong>")
                ]
            )


def invalid_language(L: str = str(), **kwargs) -> None:
    if L and L not in l10n.SUPPORTED_LANGUAGES:
        raise ValidationError(["Language is not currently supported."])


def invalid_timezone(TZ: str = str(), **kwargs) -> None:
    if TZ and TZ not in time.SUPPORTED_TIMEZONES:
        raise ValidationError(["Timezone is not currently supported."])


def username_in_use(
    U: str = str(), user: models.User = None, _: l10n.Translator = None, **kwargs
) -> None:
    exists = (
        db.query(models.User)
        .filter(
            and_(
                models.User.ID != user.ID, func.lower(models.User.Username) == U.lower()
            )
        )
        .exists()
    )
    if db.query(exists).scalar():
        # If the username already exists...
        raise ValidationError(
            [
                _("The username, %s%s%s, is already in use.")
                % ("<strong>", U, "</strong>")
            ]
        )


def email_in_use(
    E: str = str(), user: models.User = None, _: l10n.Translator = None, **kwargs
) -> None:
    exists = (
        db.query(models.User)
        .filter(
            and_(models.User.ID != user.ID, func.lower(models.User.Email) == E.lower())
        )
        .exists()
    )
    if db.query(exists).scalar():
        # If the email already exists...
        raise ValidationError(
            [
                _("The address, %s%s%s, is already in use.")
                % ("<strong>", E, "</strong>")
            ]
        )


def invalid_account_type(
    T: int = None,
    request: Request = None,
    user: models.User = None,
    _: l10n.Translator = None,
    **kwargs,
) -> None:
    if T is not None and (T := int(T)) != user.AccountTypeID:
        name = ACCOUNT_TYPE_NAME.get(T, None)
        has_cred = request.user.has_credential(creds.ACCOUNT_CHANGE_TYPE)
        if name is None:
            raise ValidationError(["Invalid account type provided."])
        elif not has_cred:
            raise ValidationError(
                ["You do not have permission to change account types."]
            )
        elif T > request.user.AccountTypeID:
            # If the chosen account type is higher than the editor's account
            # type, the editor doesn't have permission to set the new type.
            error = (
                _(
                    "You do not have permission to change "
                    "this user's account type to %s."
                )
                % name
            )
            raise ValidationError([error])

        logger.debug(
            f"Package Maintainer '{request.user.Username}' has "
            f"modified '{user.Username}' account's type to"
            f" {name}."
        )


def invalid_captcha(captcha_salt: str = None, captcha: str = None, **kwargs) -> None:
    if captcha_salt and captcha_salt not in get_captcha_salts():
        raise ValidationError(["This CAPTCHA has expired. Please try again."])

    if captcha:
        answer = get_captcha_answer(get_captcha_token(captcha_salt))
        if captcha != answer:
            raise ValidationError(["The entered CAPTCHA answer is invalid."])
