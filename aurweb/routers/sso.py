import time
import uuid

from urllib.parse import urlencode

import fastapi

from authlib.integrations.starlette_client import OAuth
from fastapi import Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.sql import select
from starlette.requests import Request

import aurweb.config
import aurweb.db

from aurweb.schema import Sessions, Users

router = fastapi.APIRouter()

oauth = OAuth()
oauth.register(
    name="sso",
    server_metadata_url=aurweb.config.get("sso", "openid_configuration"),
    client_kwargs={"scope": "openid"},
    client_id=aurweb.config.get("sso", "client_id"),
    client_secret=aurweb.config.get("sso", "client_secret"),
)


@router.get("/sso/login")
async def login(request: Request):
    """
    Redirect the user to the SSO provider’s login page.

    We specify prompt=login to force the user to input their credentials even
    if they’re already logged on the SSO. This is less practical, but given AUR
    has the potential to impact many users, better safe than sorry.
    """
    redirect_uri = aurweb.config.get("options", "aur_location") + "/sso/authenticate"
    return await oauth.sso.authorize_redirect(request, redirect_uri, prompt="login")


def open_session(conn, user_id):
    """
    Create a new user session into the database. Return its SID.
    """
    # TODO check for account suspension
    # TODO apply [options] max_sessions_per_user
    sid = uuid.uuid4().hex
    conn.execute(Sessions.insert().values(
        UsersID=user_id,
        SessionID=sid,
        LastUpdateTS=time.time(),
    ))
    # TODO update Users.LastLogin and Users.LastLoginIPAddress
    return sid


@router.get("/sso/authenticate")
async def authenticate(request: Request, conn=Depends(aurweb.db.connect)):
    """
    Receive an OpenID Connect ID token, validate it, then process it to create
    an new AUR session.
    """
    # TODO check for banned IPs
    token = await oauth.sso.authorize_access_token(request)
    user = await oauth.sso.parse_id_token(request, token)
    sub = user.get("sub")  # this is the SSO account ID in JWT terminology
    if not sub:
        raise HTTPException(status_code=400, detail="JWT is missing its `sub` field.")

    aur_accounts = conn.execute(select([Users.c.ID]).where(Users.c.SSOAccountID == sub)) \
                       .fetchall()
    if not aur_accounts:
        return "Sorry, we don’t seem to know you Sir " + sub
    elif len(aur_accounts) == 1:
        sid = open_session(conn, aur_accounts[0][Users.c.ID])
        response = RedirectResponse("/")
        # TODO redirect to the referrer
        response.set_cookie(key="AURSID", value=sid, httponly=True,
                            secure=request.url.scheme == "https")
        return response
    else:
        # We’ve got a severe integrity violation.
        raise Exception("Multiple accounts found for SSO account " + sub)


@router.get("/sso/logout")
async def logout():
    """
    Disconnect the user from the SSO provider, potentially affecting every
    other Arch service. AUR logout is performed by `/logout`, before it
    redirects to `/sso/logout`.

    Based on the OpenID Connect Session Management specification:
    https://openid.net/specs/openid-connect-session-1_0.html#RPLogout
    """
    metadata = await oauth.sso.load_server_metadata()
    # TODO Supply id_token_hint to the end session endpoint.
    query = urlencode({'post_logout_redirect_uri': aurweb.config.get('options', 'aur_location')})
    return RedirectResponse(metadata["end_session_endpoint"] + '?' + query)
