import copy
import typing

from http import HTTPStatus

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import and_, or_

import aurweb.config

from aurweb import cookies, db, l10n, logging, models, util
from aurweb.auth import account_type_required, auth_required, creds
from aurweb.captcha import get_captcha_salts
from aurweb.exceptions import ValidationError
from aurweb.l10n import get_translator_for_request
from aurweb.models import account_type as at
from aurweb.models.ssh_pub_key import get_fingerprint
from aurweb.models.user import generate_unique_resetkey
from aurweb.scripts.notify import ResetKeyNotification, WelcomeNotification
from aurweb.templates import make_context, make_variable_context, render_template
from aurweb.users import update, validate
from aurweb.users.util import get_user_by_name

router = APIRouter()
logger = logging.get_logger(__name__)


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
    context = await make_variable_context(request, "Password Reset")

    # The user parameter being required, we can match against
    user = db.query(models.User, or_(models.User.Username == user,
                                     models.User.Email == user)).first()
    if not user:
        context["errors"] = ["Invalid e-mail."]
        return render_template(request, "passreset.html", context,
                               status_code=HTTPStatus.NOT_FOUND)

    db.refresh(user)
    if resetkey:
        context["resetkey"] = resetkey

        if not user.ResetKey or resetkey != user.ResetKey:
            context["errors"] = ["Invalid e-mail."]
            return render_template(request, "passreset.html", context,
                                   status_code=HTTPStatus.NOT_FOUND)

        if not user or not password:
            context["errors"] = ["Missing a required field."]
            return render_template(request, "passreset.html", context,
                                   status_code=HTTPStatus.BAD_REQUEST)

        if password != confirm:
            # If the provided password does not match the provided confirm.
            context["errors"] = ["Password fields do not match."]
            return render_template(request, "passreset.html", context,
                                   status_code=HTTPStatus.BAD_REQUEST)

        if len(password) < models.User.minimum_passwd_length():
            # Translate the error here, which simplifies error output
            # in the jinja2 template.
            _ = get_translator_for_request(request)
            context["errors"] = [_(
                "Your password must be at least %s characters.") % (
                str(models.User.minimum_passwd_length()))]
            return render_template(request, "passreset.html", context,
                                   status_code=HTTPStatus.BAD_REQUEST)

        # We got to this point; everything matched up. Update the password
        # and remove the ResetKey.
        with db.begin():
            user.ResetKey = str()
            if user.session:
                db.delete(user.session)
            user.update_password(password)

        # Render ?step=complete.
        return RedirectResponse(url="/passreset?step=complete",
                                status_code=HTTPStatus.SEE_OTHER)

    # If we got here, we continue with issuing a resetkey for the user.
    resetkey = generate_unique_resetkey()
    with db.begin():
        user.ResetKey = resetkey

    ResetKeyNotification(user.ID).send()

    # Render ?step=confirm.
    return RedirectResponse(url="/passreset?step=confirm",
                            status_code=HTTPStatus.SEE_OTHER)


def process_account_form(request: Request, user: models.User, args: dict):
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

    checks = [
        validate.is_banned,
        validate.invalid_user_password,
        validate.invalid_fields,
        validate.invalid_suspend_permission,
        validate.invalid_username,
        validate.invalid_password,
        validate.invalid_email,
        validate.invalid_backup_email,
        validate.invalid_homepage,
        validate.invalid_pgp_key,
        validate.invalid_ssh_pubkey,
        validate.invalid_language,
        validate.invalid_timezone,
        validate.username_in_use,
        validate.email_in_use,
        validate.invalid_account_type,
        validate.invalid_captcha
    ]

    try:
        for check in checks:
            check(**args, request=request, user=user, _=_)
    except ValidationError as exc:
        return (False, exc.data)

    return (True, [])


def make_account_form_context(context: dict,
                              request: Request,
                              user: models.User,
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
        (at.USER_ID, "Normal User"),
        (at.TRUSTED_USER_ID, at.TRUSTED_USER)
    ]

    user_account_type_id = context.get("account_types")[0][0]

    if request.user.has_credential(creds.ACCOUNT_EDIT_DEV):
        context["account_types"].append((at.DEVELOPER_ID, at.DEVELOPER))
        context["account_types"].append((at.TRUSTED_USER_AND_DEV_ID,
                                         at.TRUSTED_USER_AND_DEV))

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
    context = await make_variable_context(request, "Register")
    args = dict(await request.form())

    context = make_account_form_context(context, request, None, args)
    ok, errors = process_account_form(request, request.user, args)
    if not ok:
        # If the field values given do not meet the requirements,
        # return HTTP 400 with an error.
        context["errors"] = errors
        return render_template(request, "register.html", context,
                               status_code=HTTPStatus.BAD_REQUEST)

    if not captcha:
        context["errors"] = ["The CAPTCHA is missing."]
        return render_template(request, "register.html", context,
                               status_code=HTTPStatus.BAD_REQUEST)

    # Create a user with no password with a resetkey, then send
    # an email off about it.
    resetkey = generate_unique_resetkey()

    # By default, we grab the User account type to associate with.
    atype = db.query(models.AccountType,
                     models.AccountType.AccountType == "User").first()

    # Create a user given all parameters available.
    with db.begin():
        user = db.create(models.User, Username=U,
                         Email=E, HideEmail=H, BackupEmail=BE,
                         RealName=R, Homepage=HP, IRCNick=I, PGPKey=K,
                         LangPreference=L, Timezone=TZ, CommentNotify=CN,
                         UpdateNotify=UN, OwnershipNotify=ON,
                         ResetKey=resetkey, AccountType=atype)

    # If a PK was given and either one does not exist or the given
    # PK mismatches the existing user's SSHPubKey.PubKey.
    if PK:
        # Get the second element in the PK, which is the actual key.
        pubkey = PK.strip().rstrip()
        parts = pubkey.split(" ")
        if len(parts) == 3:
            # Remove the host part.
            pubkey = parts[0] + " " + parts[1]
        fingerprint = get_fingerprint(pubkey)
        with db.begin():
            user.ssh_pub_key = models.SSHPubKey(UserID=user.ID,
                                                PubKey=pubkey,
                                                Fingerprint=fingerprint)

    # Send a reset key notification to the new user.
    WelcomeNotification(user.ID).send()

    context["complete"] = True
    context["user"] = user
    return render_template(request, "register.html", context)


def cannot_edit(request, user):
    """ Return a 401 HTMLResponse if the request user doesn't
    have authorization, otherwise None. """
    has_dev_cred = request.user.has_credential(creds.ACCOUNT_EDIT_DEV,
                                               approved=[user])
    if not has_dev_cred:
        return HTMLResponse(status_code=HTTPStatus.UNAUTHORIZED)
    return None


@router.get("/account/{username}/edit", response_class=HTMLResponse)
@auth_required(True)
async def account_edit(request: Request, username: str):
    user = db.query(models.User, models.User.Username == username).first()

    response = cannot_edit(request, user)
    if response:
        return response

    context = await make_variable_context(request, "Accounts")
    context["user"] = db.refresh(user)

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
                            T: int = Form(default=None),
                            passwd: str = Form(default=str())):
    user = db.query(models.User).filter(
        models.User.Username == username).first()
    response = cannot_edit(request, user)
    if response:
        return response

    context = await make_variable_context(request, "Accounts")
    context["user"] = db.refresh(user)

    args = dict(await request.form())
    context = make_account_form_context(context, request, user, args)
    ok, errors = process_account_form(request, user, args)

    if not passwd:
        context["errors"] = ["Invalid password."]
        return render_template(request, "account/edit.html", context,
                               status_code=HTTPStatus.BAD_REQUEST)

    if not ok:
        context["errors"] = errors
        return render_template(request, "account/edit.html", context,
                               status_code=HTTPStatus.BAD_REQUEST)

    updates = [
        update.simple,
        update.language,
        update.timezone,
        update.ssh_pubkey,
        update.account_type,
        update.password
    ]

    for f in updates:
        f(**args, request=request, user=user, context=context)

    if not errors:
        context["complete"] = True

    # Update cookies with requests, in case they were changed.
    response = render_template(request, "account/edit.html", context)
    return cookies.update_response_cookies(request, response,
                                           aurtz=TZ, aurlang=L)


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
    context = await make_variable_context(
        request, _("Account") + " " + username)
    context["user"] = get_user_by_name(username)
    return render_template(request, "account/show.html", context)


@router.get("/account/{username}/comments")
@auth_required()
async def account_comments(request: Request, username: str):
    user = get_user_by_name(username)
    context = make_context(request, "Accounts")
    context["username"] = username
    context["comments"] = user.package_comments.order_by(
        models.PackageComment.CommentTS.desc())
    return render_template(request, "account/comments.html", context)


@router.get("/accounts")
@auth_required(True)
@account_type_required({at.TRUSTED_USER,
                        at.DEVELOPER,
                        at.TRUSTED_USER_AND_DEV})
async def accounts(request: Request):
    context = make_context(request, "Accounts")
    return render_template(request, "account/search.html", context)


@router.post("/accounts")
@auth_required(True)
@account_type_required({at.TRUSTED_USER,
                        at.DEVELOPER,
                        at.TRUSTED_USER_AND_DEV})
async def accounts_post(request: Request,
                        O: int = Form(default=0),  # Offset
                        SB: str = Form(default=str()),  # Sort By
                        U: str = Form(default=str()),  # Username
                        T: str = Form(default=str()),  # Account Type
                        S: bool = Form(default=False),  # Suspended
                        E: str = Form(default=str()),  # Email
                        R: str = Form(default=str()),  # Real Name
                        I: str = Form(default=str()),  # IRC Nick
                        K: str = Form(default=str())):  # PGP Key
    context = await make_variable_context(request, "Accounts")
    context["pp"] = pp = 50  # Hits per page.

    offset = max(O, 0)  # Minimize offset at 0.
    context["offset"] = offset  # Offset.

    context["params"] = dict(await request.form())
    if "O" in context["params"]:
        context["params"].pop("O")

    # Setup order by criteria based on SB.
    order_by_columns = {
        "t": (models.AccountType.ID.asc(), models.User.Username.asc()),
        "r": (models.User.RealName.asc(), models.AccountType.ID.asc()),
        "i": (models.User.IRCNick.asc(), models.AccountType.ID.asc()),
    }
    default_order = (models.User.Username.asc(), models.AccountType.ID.asc())
    order_by = order_by_columns.get(SB, default_order)

    # Convert parameter T to an AccountType ID.
    account_types = {
        "u": at.USER_ID,
        "t": at.TRUSTED_USER_ID,
        "d": at.DEVELOPER_ID,
        "td": at.TRUSTED_USER_AND_DEV_ID
    }
    account_type_id = account_types.get(T, None)

    # Get a query handle to users, populate the total user
    # count into a jinja2 context variable.
    query = db.query(models.User).join(models.AccountType)
    context["total_users"] = query.count()

    # Populate this list with any additional statements to
    # be ANDed together.
    statements = [
        v for k, v in [
            (account_type_id is not None, models.AccountType.ID == account_type_id),
            (bool(U), models.User.Username.like(f"%{U}%")),
            (bool(S), models.User.Suspended == S),
            (bool(E), models.User.Email.like(f"%{E}%")),
            (bool(R), models.User.RealName.like(f"%{R}%")),
            (bool(I), models.User.IRCNick.like(f"%{I}%")),
            (bool(K), models.User.PGPKey.like(f"%{K}%")),
        ] if k
    ]

    # Filter the query by coe-mbining all statements added above into
    # an AND statement, unless there's just one statement, which
    # we pass on to filter() as args.
    if statements:
        query = query.filter(and_(*statements))

    # Finally, order and truncate our users for the current page.
    users = query.order_by(*order_by).limit(pp).offset(offset)
    context["users"] = util.apply_all(users, db.refresh)

    return render_template(request, "account/index.html", context)


def render_terms_of_service(request: Request,
                            context: dict,
                            terms: typing.Iterable):
    if not terms:
        return RedirectResponse("/", status_code=HTTPStatus.SEE_OTHER)
    context["unaccepted_terms"] = terms
    return render_template(request, "tos/index.html", context)


@router.get("/tos")
@auth_required(True)
async def terms_of_service(request: Request):
    # Query the database for terms that were previously accepted,
    # but now have a bumped Revision that needs to be accepted.
    diffs = db.query(models.Term).join(models.AcceptedTerm).filter(
        models.AcceptedTerm.Revision < models.Term.Revision).all()

    # Query the database for any terms that have not yet been accepted.
    unaccepted = db.query(models.Term).filter(
        ~models.Term.ID.in_(db.query(models.AcceptedTerm.TermsID))).all()

    for record in (diffs + unaccepted):
        db.refresh(record)

    # Translate the 'Terms of Service' part of our page title.
    _ = l10n.get_translator_for_request(request)
    title = f"AUR {_('Terms of Service')}"
    context = await make_variable_context(request, title)

    accept_needed = sorted(unaccepted + diffs)
    return render_terms_of_service(request, context, accept_needed)


@router.post("/tos")
@auth_required(True)
async def terms_of_service_post(request: Request,
                                accept: bool = Form(default=False)):
    # Query the database for terms that were previously accepted,
    # but now have a bumped Revision that needs to be accepted.
    diffs = db.query(models.Term).join(models.AcceptedTerm).filter(
        models.AcceptedTerm.Revision < models.Term.Revision).all()

    # Query the database for any terms that have not yet been accepted.
    unaccepted = db.query(models.Term).filter(
        ~models.Term.ID.in_(db.query(models.AcceptedTerm.TermsID))).all()

    if not accept:
        # Translate the 'Terms of Service' part of our page title.
        _ = l10n.get_translator_for_request(request)
        title = f"AUR {_('Terms of Service')}"
        context = await make_variable_context(request, title)

        # We already did the database filters here, so let's just use
        # them instead of reiterating the process in terms_of_service.
        accept_needed = sorted(unaccepted + diffs)
        return render_terms_of_service(
            request, context, util.apply_all(accept_needed, db.refresh))

    with db.begin():
        # For each term we found, query for the matching accepted term
        # and update its Revision to the term's current Revision.
        for term in diffs:
            db.refresh(term)
            accepted_term = request.user.accepted_terms.filter(
                models.AcceptedTerm.TermsID == term.ID).first()
            accepted_term.Revision = term.Revision

        # For each term that was never accepted, accept it!
        for term in unaccepted:
            db.refresh(term)
            db.create(models.AcceptedTerm, User=request.user,
                      Term=term, Revision=term.Revision)

    return RedirectResponse("/", status_code=HTTPStatus.SEE_OTHER)
