from http import HTTPStatus

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import or_

from aurweb import db
from aurweb.auth import auth_required
from aurweb.l10n import get_translator_for_request
from aurweb.models.user import User
from aurweb.scripts.notify import ResetKeyNotification
from aurweb.templates import make_context, render_template

router = APIRouter()


@router.get("/passreset", response_class=HTMLResponse)
@auth_required(False)
async def passreset(request: Request):
    context = make_context(request, "Password Reset")

    for k, v in request.query_params.items():
        context[k] = v

    return render_template(request, "passreset.html", context)


@router.post("/passreset", response_class=HTMLResponse)
@auth_required(False)
async def passreset_post(request: Request,
                         user: str = Form(...),
                         resetkey: str = Form(default=None),
                         password: str = Form(default=None),
                         confirm: str = Form(default=None)):
    from aurweb.db import session

    context = make_context(request, "Password Reset")

    for k, v in dict(await request.form()).items():
        context[k] = v

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
