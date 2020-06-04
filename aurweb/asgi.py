from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

import aurweb.config

from aurweb.routers import sso

app = FastAPI()

session_secret = aurweb.config.get("fastapi", "session_secret")
if not session_secret:
    raise Exception("[fastapi] session_secret must not be empty")

app.add_middleware(SessionMiddleware, secret_key=session_secret)

app.include_router(sso.router)
