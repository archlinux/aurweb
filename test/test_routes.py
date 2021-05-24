import urllib.parse

from http import HTTPStatus

import pytest

from fastapi.testclient import TestClient

from aurweb.asgi import app
from aurweb.db import query
from aurweb.models.account_type import AccountType
from aurweb.testing import setup_test_db
from aurweb.testing.models import make_user
from aurweb.testing.requests import Request

client = TestClient(app)
user = None


@pytest.fixture(autouse=True)
def setup():
    global user

    setup_test_db("Users", "Sessions")

    account_type = query(AccountType,
                         AccountType.AccountType == "User").first()
    user = make_user(Username="test", Email="test@example.org",
                     RealName="Test User", Passwd="testPassword",
                     AccountType=account_type)


def test_index():
    """ Test the index route at '/'. """
    # Use `with` to trigger FastAPI app events.
    with client as req:
        response = req.get("/")
    assert response.status_code == int(HTTPStatus.OK)


def test_favicon():
    """ Test the favicon route at '/favicon.ico'. """
    response1 = client.get("/static/images/favicon.ico")
    response2 = client.get("/favicon.ico")
    assert response1.status_code == int(HTTPStatus.OK)
    assert response1.content == response2.content


def test_language():
    """ Test the language post route as a guest user. """
    post_data = {
        "set_lang": "de",
        "next": "/"
    }
    with client as req:
        response = req.post("/language", data=post_data)
    assert response.status_code == int(HTTPStatus.SEE_OTHER)


def test_language_invalid_next():
    """ Test an invalid next route at '/language'. """
    post_data = {
        "set_lang": "de",
        "next": "https://evil.net"
    }
    with client as req:
        response = req.post("/language", data=post_data)
    assert response.status_code == int(HTTPStatus.BAD_REQUEST)


def test_user_language():
    """ Test the language post route as an authenticated user. """
    post_data = {
        "set_lang": "de",
        "next": "/"
    }

    sid = user.login(Request(), "testPassword")
    assert sid is not None

    with client as req:
        response = req.post("/language", data=post_data,
                            cookies={"AURSID": sid})
    assert response.status_code == int(HTTPStatus.SEE_OTHER)
    assert user.LangPreference == "de"


def test_language_query_params():
    """ Test the language post route with query params. """
    next = urllib.parse.quote_plus("/")
    post_data = {
        "set_lang": "de",
        "next": "/",
        "q": f"next={next}"
    }
    q = post_data.get("q")
    with client as req:
        response = req.post("/language", data=post_data)
        assert response.headers.get("location") == f"/?{q}"
    assert response.status_code == int(HTTPStatus.SEE_OTHER)


def test_error_messages():
    response1 = client.get("/thisroutedoesnotexist")
    response2 = client.get("/raisefivethree")
    assert response1.status_code == int(HTTPStatus.NOT_FOUND)
    assert response2.status_code == int(HTTPStatus.SERVICE_UNAVAILABLE)
