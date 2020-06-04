import fastapi

from authlib.integrations.starlette_client import OAuth
from starlette.requests import Request

import aurweb.config

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
    redirect_uri = aurweb.config.get("options", "aur_location") + "/sso/authenticate"
    return await oauth.sso.authorize_redirect(request, redirect_uri, prompt="login")


@router.get("/sso/authenticate")
async def authenticate(request: Request):
    token = await oauth.sso.authorize_access_token(request)
    user = await oauth.sso.parse_id_token(request, token)
    return dict(user)
