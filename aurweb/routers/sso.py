import time
import uuid

from urllib.parse import urlencode

import fastapi

from authlib.integrations.starlette_client import OAuth, OAuthError
from fastapi import Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.sql import select
from starlette.requests import Request

import aurweb.config
import aurweb.db

from aurweb.l10n import get_translator_for_request
from aurweb.schema import Bans, Sessions, Users

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


def is_account_suspended(conn, user_id):
    row = conn.execute(select([Users.c.Suspended]).where(Users.c.ID == user_id)).fetchone()
    return row is not None and bool(row[0])


def open_session(request, conn, user_id):
    """
    Create a new user session into the database. Return its SID.
    """
    if is_account_suspended(conn, user_id):
        _ = get_translator_for_request(request)
        raise HTTPException(status_code=403, detail=_('Account suspended'))
        # TODO This is a terrible message because it could imply the attempt at
        #      logging in just caused the suspension.

    sid = uuid.uuid4().hex
    conn.execute(Sessions.insert().values(
        UsersID=user_id,
        SessionID=sid,
        LastUpdateTS=time.time(),
    ))

    # Update user’s last login information.
    conn.execute(Users.update()
                      .where(Users.c.ID == user_id)
                      .values(LastLogin=int(time.time()),
                              LastLoginIPAddress=request.client.host))

    return sid


def is_ip_banned(conn, ip):
    """
    Check if an IP is banned. `ip` is a string and may be an IPv4 as well as an
    IPv6, depending on the server’s configuration.
    """
    result = conn.execute(Bans.select().where(Bans.c.IPAddress == ip))
    return result.fetchone() is not None


@router.get("/sso/authenticate")
async def authenticate(request: Request, conn=Depends(aurweb.db.connect)):
    """
    Receive an OpenID Connect ID token, validate it, then process it to create
    an new AUR session.
    """
    if is_ip_banned(conn, request.client.host):
        _ = get_translator_for_request(request)
        raise HTTPException(
            status_code=403,
            detail=_('The login form is currently disabled for your IP address, '
                     'probably due to sustained spam attacks. Sorry for the '
                     'inconvenience.'))

    try:
        token = await oauth.sso.authorize_access_token(request)
        user = await oauth.sso.parse_id_token(request, token)
    except OAuthError:
        # Here, most OAuth errors should be caused by forged or expired tokens.
        # Let’s give attackers as little information as possible.
        _ = get_translator_for_request(request)
        raise HTTPException(
            status_code=400,
            detail=_('Bad OAuth token. Please retry logging in from the start.'))

    sub = user.get("sub")  # this is the SSO account ID in JWT terminology
    if not sub:
        _ = get_translator_for_request(request)
        raise HTTPException(status_code=400, detail=_("JWT is missing its `sub` field."))

    aur_accounts = conn.execute(select([Users.c.ID]).where(Users.c.SSOAccountID == sub)) \
                       .fetchall()
    if not aur_accounts:
        return "Sorry, we don’t seem to know you Sir " + sub
    elif len(aur_accounts) == 1:
        sid = open_session(request, conn, aur_accounts[0][Users.c.ID])
        response = RedirectResponse("/")
        # TODO redirect to the referrer
        response.set_cookie(key="AURSID", value=sid, httponly=True,
                            secure=request.url.scheme == "https")
        if "id_token" in token:
            # We save the id_token for the SSO logout. It’s not too important
            # though, so if we can’t find it, we can live without it.
            response.set_cookie(key="SSO_ID_TOKEN", value=token["id_token"], path="/sso/",
                                httponly=True, secure=request.url.scheme == "https")
        return response
    else:
        # We’ve got a severe integrity violation.
        raise Exception("Multiple accounts found for SSO account " + sub)


@router.get("/sso/logout")
async def logout(request: Request):
    """
    Disconnect the user from the SSO provider, potentially affecting every
    other Arch service. AUR logout is performed by `/logout`, before it
    redirects to `/sso/logout`.

    Based on the OpenID Connect Session Management specification:
    https://openid.net/specs/openid-connect-session-1_0.html#RPLogout
    """
    id_token = request.cookies.get("SSO_ID_TOKEN")
    if not id_token:
        return RedirectResponse("/")

    metadata = await oauth.sso.load_server_metadata()
    query = urlencode({'post_logout_redirect_uri': aurweb.config.get('options', 'aur_location'),
                       'id_token_hint': id_token})
    response = RedirectResponse(metadata["end_session_endpoint"] + '?' + query)
    response.delete_cookie("SSO_ID_TOKEN", path="/sso/")
    return response
