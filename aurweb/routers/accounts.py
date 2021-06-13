import copy
import typing

from datetime import datetime
from http import HTTPStatus

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import and_, func, or_

import aurweb.config

from aurweb import db, l10n, time, util
from aurweb.auth import auth_required
from aurweb.captcha import get_captcha_answer, get_captcha_salts, get_captcha_token
from aurweb.l10n import get_translator_for_request
from aurweb.models.accepted_term import AcceptedTerm
from aurweb.models.account_type import AccountType
from aurweb.models.ban import Ban
from aurweb.models.ssh_pub_key import SSHPubKey, get_fingerprint
from aurweb.models.term import Term
from aurweb.models.user import User
from aurweb.scripts.notify import ResetKeyNotification
from aurweb.templates import make_variable_context, render_template

router = APIRouter()


@router.get("/passreset", response_class=HTMLResponse)
@auth_required(False)
async def passreset(request: Request):
    context = await make_variable_context(request, "Password Reset")
    return render_template(request, "passreset.html", context)


@router.post("/passreset", response_class=HTMLResponse)
@auth_required(False)
async def passreset_post(request: Request,
                         user: str = Form(...),
                         resetkey: str = Form(default=None),
                         password: str = Form(default=None),
                         confirm: str = Form(default=None)):
    from aurweb.db import session

    context = await make_variable_context(request, "Password Reset")

    # The user parameter being required, we can match against
    user = db.query(User, or_(User.Username == user,
                              User.Email == user)).first()
    if not user:
        context["errors"] = ["Invalid e-mail."]
        return render_template(request, "passreset.html", context,
                               status_code=int(HTTPStatus.NOT_FOUND))

    if resetkey:
        context["resetkey"] = resetkey

        if not user.ResetKey or resetkey != user.ResetKey:
            context["errors"] = ["Invalid e-mail."]
            return render_template(request, "passreset.html", context,
                                   status_code=int(HTTPStatus.NOT_FOUND))

        if not user or not password:
            context["errors"] = ["Missing a required field."]
            return render_template(request, "passreset.html", context,
                                   status_code=int(HTTPStatus.BAD_REQUEST))

        if password != confirm:
            # If the provided password does not match the provided confirm.
            context["errors"] = ["Password fields do not match."]
            return render_template(request, "passreset.html", context,
                                   status_code=int(HTTPStatus.BAD_REQUEST))

        if len(password) < User.minimum_passwd_length():
            # Translate the error here, which simplifies error output
            # in the jinja2 template.
            _ = get_translator_for_request(request)
            context["errors"] = [_(
                "Your password must be at least %s characters.") % (
                str(User.minimum_passwd_length()))]
            return render_template(request, "passreset.html", context,
                                   status_code=int(HTTPStatus.BAD_REQUEST))

        # We got to this point; everything matched up. Update the password
        # and remove the ResetKey.
        user.ResetKey = str()
        user.update_password(password)

        if user.session:
            session.delete(user.session)
            session.commit()

        # Render ?step=complete.
        return RedirectResponse(url="/passreset?step=complete",
                                status_code=int(HTTPStatus.SEE_OTHER))

    # If we got here, we continue with issuing a resetkey for the user.
    resetkey = db.make_random_value(User, User.ResetKey)
    user.ResetKey = resetkey
    session.commit()

    executor = db.ConnectionExecutor(db.get_engine().raw_connection())
    ResetKeyNotification(executor, user.ID).send()

    # Render ?step=confirm.
    return RedirectResponse(url="/passreset?step=confirm",
                            status_code=int(HTTPStatus.SEE_OTHER))


def process_account_form(request: Request, user: User, args: dict):
    """ Process an account form. All fields are optional and only checks
    requirements in the case they are present.

    ```
    context = await make_variable_context(request, "Accounts")
    ok, errors = process_account_form(request, user, **kwargs)
    if not ok:
        context["errors"] = errors
        return render_template(request, "some_account_template.html", context)
    ```

    :param request: An incoming FastAPI request
    :param user: The user model of the account being processed
    :param args: A dictionary of arguments generated via request.form()
    :return: A (passed processing boolean, list of errors) tuple
    """

    # Get a local translator.
    _ = get_translator_for_request(request)

    host = request.client.host
    ban = db.query(Ban, Ban.IPAddress == host).first()
    if ban:
        return False, [
            "Account registration has been disabled for your " +
            "IP address, probably due to sustained spam attacks. " +
            "Sorry for the inconvenience."
        ]

    if request.user.is_authenticated():
        if not request.user.valid_password(args.get("passwd", None)):
            return False, ["Invalid password."]

    email = args.get("E", None)
    username = args.get("U", None)

    if not email or not username:
        return False, ["Missing a required field."]

    username_min_len = aurweb.config.getint("options", "username_min_len")
    username_max_len = aurweb.config.getint("options", "username_max_len")
    if not util.valid_username(args.get("U")):
        return False, [
            "The username is invalid.",
            [
                _("It must be between %s and %s characters long") % (
                    username_min_len, username_max_len),
                "Start and end with a letter or number",
                "Can contain only one period, underscore or hyphen.",
            ]
        ]

    password = args.get("P", None)
    if password:
        confirmation = args.get("C", None)
        if not util.valid_password(password):
            return False, [
                _("Your password must be at least %s characters.") % (
                    username_min_len)
            ]
        elif not confirmation:
            return False, ["Please confirm your new password."]
        elif password != confirmation:
            return False, ["Password fields do not match."]

    backup_email = args.get("BE", None)
    homepage = args.get("HP", None)
    pgp_key = args.get("K", None)
    ssh_pubkey = args.get("PK", None)
    language = args.get("L", None)
    timezone = args.get("TZ", None)

    def username_exists(username):
        return and_(User.ID != user.ID,
                    func.lower(User.Username) == username.lower())

    def email_exists(email):
        return and_(User.ID != user.ID,
                    func.lower(User.Email) == email.lower())

    if not util.valid_email(email):
        return False, ["The email address is invalid."]
    elif backup_email and not util.valid_email(backup_email):
        return False, ["The backup email address is invalid."]
    elif homepage and not util.valid_homepage(homepage):
        return False, [
            "The home page is invalid, please specify the full HTTP(s) URL."]
    elif pgp_key and not util.valid_pgp_fingerprint(pgp_key):
        return False, ["The PGP key fingerprint is invalid."]
    elif ssh_pubkey and not util.valid_ssh_pubkey(ssh_pubkey):
        return False, ["The SSH public key is invalid."]
    elif language and language not in l10n.SUPPORTED_LANGUAGES:
        return False, ["Language is not currently supported."]
    elif timezone and timezone not in time.SUPPORTED_TIMEZONES:
        return False, ["Timezone is not currently supported."]
    elif db.query(User, username_exists(username)).first():
        # If the username already exists...
        return False, [
            _("The username, %s%s%s, is already in use.") % (
                "<strong>", username, "</strong>")
        ]
    elif db.query(User, email_exists(email)).first():
        # If the email already exists...
        return False, [
            _("The address, %s%s%s, is already in use.") % (
                "<strong>", email, "</strong>")
        ]

    def ssh_fingerprint_exists(fingerprint):
        return and_(SSHPubKey.UserID != user.ID,
                    SSHPubKey.Fingerprint == fingerprint)

    if ssh_pubkey:
        fingerprint = get_fingerprint(ssh_pubkey.strip().rstrip())
        if fingerprint is None:
            return False, ["The SSH public key is invalid."]

        if db.query(SSHPubKey, ssh_fingerprint_exists(fingerprint)).first():
            return False, [
                _("The SSH public key, %s%s%s, is already in use.") % (
                    "<strong>", fingerprint, "</strong>")
            ]

    captcha_salt = args.get("captcha_salt", None)
    if captcha_salt and captcha_salt not in get_captcha_salts():
        return False, ["This CAPTCHA has expired. Please try again."]

    captcha = args.get("captcha", None)
    if captcha:
        answer = get_captcha_answer(get_captcha_token(captcha_salt))
        if captcha != answer:
            return False, ["The entered CAPTCHA answer is invalid."]

    return True, []


def make_account_form_context(context: dict,
                              request: Request,
                              user: User,
                              args: dict):
    """ Modify a FastAPI context and add attributes for the account form.

    :param context: FastAPI context
    :param request: FastAPI request
    :param user: Target user
    :param args: Persistent arguments: request.form()
    :return: FastAPI context adjusted for account form
    """
    # Do not modify the original context.
    context = copy.copy(context)

    context["account_types"] = [
        (1, "Normal User"),
        (2, "Trusted User")
    ]

    user_account_type_id = context.get("account_types")[0][0]

    if request.user.has_credential("CRED_ACCOUNT_EDIT_DEV"):
        context["account_types"].append((3, "Developer"))
        context["account_types"].append((4, "Trusted User & Developer"))

    if request.user.is_authenticated():
        context["username"] = args.get("U", user.Username)
        context["account_type"] = args.get("T", user.AccountType.ID)
        context["suspended"] = args.get("S", user.Suspended)
        context["email"] = args.get("E", user.Email)
        context["hide_email"] = args.get("H", user.HideEmail)
        context["backup_email"] = args.get("BE", user.BackupEmail)
        context["realname"] = args.get("R", user.RealName)
        context["homepage"] = args.get("HP", user.Homepage or str())
        context["ircnick"] = args.get("I", user.IRCNick)
        context["pgp"] = args.get("K", user.PGPKey or str())
        context["lang"] = args.get("L", user.LangPreference)
        context["tz"] = args.get("TZ", user.Timezone)
        ssh_pk = user.ssh_pub_key.PubKey if user.ssh_pub_key else str()
        context["ssh_pk"] = args.get("PK", ssh_pk)
        context["cn"] = args.get("CN", user.CommentNotify)
        context["un"] = args.get("UN", user.UpdateNotify)
        context["on"] = args.get("ON", user.OwnershipNotify)
        context["inactive"] = args.get("J", user.InactivityTS != 0)
    else:
        context["username"] = args.get("U", str())
        context["account_type"] = args.get("T", user_account_type_id)
        context["suspended"] = args.get("S", False)
        context["email"] = args.get("E", str())
        context["hide_email"] = args.get("H", False)
        context["backup_email"] = args.get("BE", str())
        context["realname"] = args.get("R", str())
        context["homepage"] = args.get("HP", str())
        context["ircnick"] = args.get("I", str())
        context["pgp"] = args.get("K", str())
        context["lang"] = args.get("L", context.get("language"))
        context["tz"] = args.get("TZ", context.get("timezone"))
        context["ssh_pk"] = args.get("PK", str())
        context["cn"] = args.get("CN", True)
        context["un"] = args.get("UN", False)
        context["on"] = args.get("ON", True)
        context["inactive"] = args.get("J", False)

    context["password"] = args.get("P", str())
    context["confirm"] = args.get("C", str())

    return context


@router.get("/register", response_class=HTMLResponse)
@auth_required(False)
async def account_register(request: Request,
                           U: str = Form(default=str()),    # Username
                           E: str = Form(default=str()),    # Email
                           H: str = Form(default=False),    # Hide Email
                           BE: str = Form(default=None),    # Backup Email
                           R: str = Form(default=None),     # Real Name
                           HP: str = Form(default=None),    # Homepage
                           I: str = Form(default=None),     # IRC Nick
                           K: str = Form(default=None),     # PGP Key FP
                           L: str = Form(default=aurweb.config.get(
                               "options", "default_lang")),
                           TZ: str = Form(default=aurweb.config.get(
                               "options", "default_timezone")),
                           PK: str = Form(default=None),
                           CN: bool = Form(default=False),  # Comment Notify
                           CU: bool = Form(default=False),  # Update Notify
                           CO: bool = Form(default=False),  # Owner Notify
                           captcha: str = Form(default=str())):
    context = await make_variable_context(request, "Register")
    context["captcha_salt"] = get_captcha_salts()[0]
    context = make_account_form_context(context, request, None, dict())
    return render_template(request, "register.html", context)


@router.post("/register", response_class=HTMLResponse)
@auth_required(False)
async def account_register_post(request: Request,
                                U: str = Form(default=str()),  # Username
                                E: str = Form(default=str()),  # Email
                                H: str = Form(default=False),   # Hide Email
                                BE: str = Form(default=None),   # Backup Email
                                R: str = Form(default=''),    # Real Name
                                HP: str = Form(default=None),   # Homepage
                                I: str = Form(default=None),    # IRC Nick
                                K: str = Form(default=None),    # PGP Key
                                L: str = Form(default=aurweb.config.get(
                                    "options", "default_lang")),
                                TZ: str = Form(default=aurweb.config.get(
                                    "options", "default_timezone")),
                                PK: str = Form(default=None),   # SSH PubKey
                                CN: bool = Form(default=False),
                                UN: bool = Form(default=False),
                                ON: bool = Form(default=False),
                                captcha: str = Form(default=None),
                                captcha_salt: str = Form(...)):
    from aurweb.db import session

    context = await make_variable_context(request, "Register")

    args = dict(await request.form())
    context = make_account_form_context(context, request, None, args)

    ok, errors = process_account_form(request, request.user, args)

    if not ok:
        # If the field values given do not meet the requirements,
        # return HTTP 400 with an error.
        context["errors"] = errors
        return render_template(request, "register.html", context,
                               status_code=int(HTTPStatus.BAD_REQUEST))

    if not captcha:
        context["errors"] = ["The CAPTCHA is missing."]
        return render_template(request, "register.html", context,
                               status_code=int(HTTPStatus.BAD_REQUEST))

    # Create a user with no password with a resetkey, then send
    # an email off about it.
    resetkey = db.make_random_value(User, User.ResetKey)

    # By default, we grab the User account type to associate with.
    account_type = db.query(AccountType,
                            AccountType.AccountType == "User").first()

    # Create a user given all parameters available.
    user = db.create(User, Username=U, Email=E, HideEmail=H, BackupEmail=BE,
                     RealName=R, Homepage=HP, IRCNick=I, PGPKey=K,
                     LangPreference=L, Timezone=TZ, CommentNotify=CN,
                     UpdateNotify=UN, OwnershipNotify=ON, ResetKey=resetkey,
                     AccountType=account_type)

    # If a PK was given and either one does not exist or the given
    # PK mismatches the existing user's SSHPubKey.PubKey.
    if PK:
        # Get the second element in the PK, which is the actual key.
        pubkey = PK.strip().rstrip()
        fingerprint = get_fingerprint(pubkey)
        user.ssh_pub_key = SSHPubKey(UserID=user.ID,
                                     PubKey=pubkey,
                                     Fingerprint=fingerprint)
        session.commit()

    # Send a reset key notification to the new user.
    executor = db.ConnectionExecutor(db.get_engine().raw_connection())
    ResetKeyNotification(executor, user.ID).send()

    context["complete"] = True
    context["user"] = user
    return render_template(request, "register.html", context)


def cannot_edit(request, user):
    """ Return a 401 HTMLResponse if the request user doesn't
    have authorization, otherwise None. """
    has_dev_cred = request.user.has_credential("CRED_ACCOUNT_EDIT_DEV",
                                               approved=[user])
    if not has_dev_cred:
        return HTMLResponse(status_code=int(HTTPStatus.UNAUTHORIZED))
    return None


@router.get("/account/{username}/edit", response_class=HTMLResponse)
@auth_required(True)
async def account_edit(request: Request,
                       username: str):
    user = db.query(User, User.Username == username).first()
    response = cannot_edit(request, user)
    if response:
        return response

    context = await make_variable_context(request, "Accounts")
    context["user"] = user

    context = make_account_form_context(context, request, user, dict())
    return render_template(request, "account/edit.html", context)


@router.post("/account/{username}/edit", response_class=HTMLResponse)
@auth_required(True)
async def account_edit_post(request: Request,
                            username: str,
                            U: str = Form(default=str()),  # Username
                            J: bool = Form(default=False),
                            E: str = Form(default=str()),  # Email
                            H: str = Form(default=False),    # Hide Email
                            BE: str = Form(default=None),    # Backup Email
                            R: str = Form(default=None),     # Real Name
                            HP: str = Form(default=None),    # Homepage
                            I: str = Form(default=None),     # IRC Nick
                            K: str = Form(default=None),     # PGP Key
                            L: str = Form(aurweb.config.get(
                                "options", "default_lang")),
                            TZ: str = Form(aurweb.config.get(
                                "options", "default_timezone")),
                            P: str = Form(default=str()),    # New Password
                            C: str = Form(default=None),     # Password Confirm
                            PK: str = Form(default=None),    # PubKey
                            CN: bool = Form(default=False),  # Comment Notify
                            UN: bool = Form(default=False),  # Update Notify
                            ON: bool = Form(default=False),  # Owner Notify
                            passwd: str = Form(default=str())):
    from aurweb.db import session

    user = session.query(User).filter(User.Username == username).first()
    response = cannot_edit(request, user)
    if response:
        return response

    context = await make_variable_context(request, "Accounts")
    context["user"] = user

    if not passwd:
        context["errors"] = ["Invalid password."]
        return render_template(request, "account/edit.html", context,
                               status_code=int(HTTPStatus.BAD_REQUEST))

    args = dict(await request.form())
    context = make_account_form_context(context, request, user, args)
    ok, errors = process_account_form(request, user, args)

    if not ok:
        context["errors"] = errors
        return render_template(request, "account/edit.html", context,
                               status_code=int(HTTPStatus.BAD_REQUEST))

    # Set all updated fields as needed.
    user.Username = U or user.Username
    user.Email = E or user.Email
    user.HideEmail = bool(H)
    user.BackupEmail = BE or user.BackupEmail
    user.RealName = R or user.RealName
    user.Homepage = HP or user.Homepage
    user.IRCNick = I or user.IRCNick
    user.PGPKey = K or user.PGPKey
    user.InactivityTS = datetime.utcnow().timestamp() if J else 0

    # If we update the language, update the cookie as well.
    if L and L != user.LangPreference:
        request.cookies["AURLANG"] = L
        user.LangPreference = L
        context["language"] = L

    # If we update the timezone, also update the cookie.
    if TZ and TZ != user.Timezone:
        user.Timezone = TZ
        request.cookies["AURTZ"] = TZ
        context["timezone"] = TZ

    user.CommentNotify = bool(CN)
    user.UpdateNotify = bool(UN)
    user.OwnershipNotify = bool(ON)

    # If a PK is given, compare it against the target user's PK.
    if PK:
        # Get the second token in the public key, which is the actual key.
        pubkey = PK.strip().rstrip()
        fingerprint = get_fingerprint(pubkey)
        if not user.ssh_pub_key:
            # No public key exists, create one.
            user.ssh_pub_key = SSHPubKey(UserID=user.ID,
                                         PubKey=PK,
                                         Fingerprint=fingerprint)
        elif user.ssh_pub_key.Fingerprint != fingerprint:
            # A public key already exists, update it.
            user.ssh_pub_key.PubKey = PK
            user.ssh_pub_key.Fingerprint = fingerprint
    elif user.ssh_pub_key:
        # Else, if the user has a public key already, delete it.
        session.delete(user.ssh_pub_key)

    # Commit changes, if any.
    session.commit()

    if P and not user.valid_password(P):
        # Remove the fields we consumed for passwords.
        context["P"] = context["C"] = str()

        # If a password was given and it doesn't match the user's, update it.
        user.update_password(P)
        if user == request.user:
            # If the target user is the request user, login with
            # the updated password and update AURSID.
            request.cookies["AURSID"] = user.login(request, P)

    if not errors:
        context["complete"] = True

    # Update cookies with requests, in case they were changed.
    response = render_template(request, "account/edit.html", context)
    return util.migrate_cookies(request, response)


account_template = (
    "account/show.html",
    ["Account", "{}"],
    ["username"]  # Query parameters to replace in the title string.
)


@router.get("/account/{username}")
@auth_required(True, template=account_template,
               status_code=HTTPStatus.UNAUTHORIZED)
async def account(request: Request, username: str):
    _ = l10n.get_translator_for_request(request)
    context = await make_variable_context(request, _("Account") + username)

    user = db.query(User, User.Username == username).first()
    if not user:
        raise HTTPException(status_code=int(HTTPStatus.NOT_FOUND))

    context["user"] = user

    return render_template(request, "account/show.html", context)


def render_terms_of_service(request: Request,
                            context: dict,
                            terms: typing.Iterable):
    if not terms:
        return RedirectResponse("/", status_code=int(HTTPStatus.SEE_OTHER))
    context["unaccepted_terms"] = terms
    return render_template(request, "tos/index.html", context)


@router.get("/tos")
@auth_required(True, redirect="/")
async def terms_of_service(request: Request):
    # Query the database for terms that were previously accepted,
    # but now have a bumped Revision that needs to be accepted.
    diffs = db.query(Term).join(AcceptedTerm).filter(
        AcceptedTerm.Revision < Term.Revision).all()

    # Query the database for any terms that have not yet been accepted.
    unaccepted = db.query(Term).filter(
        ~Term.ID.in_(db.query(AcceptedTerm.TermsID))).all()

    # Translate the 'Terms of Service' part of our page title.
    _ = l10n.get_translator_for_request(request)
    title = f"AUR {_('Terms of Service')}"
    context = await make_variable_context(request, title)

    accept_needed = sorted(unaccepted + diffs)
    return render_terms_of_service(request, context, accept_needed)


@router.post("/tos")
@auth_required(True, redirect="/")
async def terms_of_service_post(request: Request,
                                accept: bool = Form(default=False)):
    # Query the database for terms that were previously accepted,
    # but now have a bumped Revision that needs to be accepted.
    diffs = db.query(Term).join(AcceptedTerm).filter(
        AcceptedTerm.Revision < Term.Revision).all()

    # Query the database for any terms that have not yet been accepted.
    unaccepted = db.query(Term).filter(
        ~Term.ID.in_(db.query(AcceptedTerm.TermsID))).all()

    if not accept:
        # Translate the 'Terms of Service' part of our page title.
        _ = l10n.get_translator_for_request(request)
        title = f"AUR {_('Terms of Service')}"
        context = await make_variable_context(request, title)

        # We already did the database filters here, so let's just use
        # them instead of reiterating the process in terms_of_service.
        accept_needed = sorted(unaccepted + diffs)
        return render_terms_of_service(request, context, accept_needed)

    # For each term we found, query for the matching accepted term
    # and update its Revision to the term's current Revision.
    for term in diffs:
        accepted_term = request.user.accepted_terms.filter(
            AcceptedTerm.TermsID == term.ID).first()
        accepted_term.Revision = term.Revision

    # For each term that was never accepted, accept it!
    for term in unaccepted:
        db.create(AcceptedTerm, User=request.user,
                  Term=term, Revision=term.Revision,
                  autocommit=False)

    if diffs or unaccepted:
        # If we had any terms to update, commit the changes.
        db.commit()

    return RedirectResponse("/", status_code=int(HTTPStatus.SEE_OTHER))
