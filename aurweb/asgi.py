import http

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from starlette.middleware.sessions import SessionMiddleware

import aurweb.config

from aurweb.routers import sso

app = FastAPI()

session_secret = aurweb.config.get("fastapi", "session_secret")
if not session_secret:
    raise Exception("[fastapi] session_secret must not be empty")

app.add_middleware(SessionMiddleware, secret_key=session_secret)

app.include_router(sso.router)


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """
    Dirty HTML error page to replace the default JSON error responses.
    In the future this should use a proper Arch-themed HTML template.
    """
    phrase = http.HTTPStatus(exc.status_code).phrase
    return HTMLResponse(f"<h1>{exc.status_code} {phrase}</h1><p>{exc.detail}</p>",
                        status_code=exc.status_code)
