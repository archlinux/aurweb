import asyncio
from typing import Generator

import pytest
from httpx import ASGITransport, AsyncClient

import aurweb.config
from aurweb import db
from aurweb.asgi import app
from aurweb.models.account_type import USER_ID
from aurweb.models.user import User

NUM_USERS = 8
LOGINS_PER_USER = 4


@pytest.fixture(autouse=True)
def setup(db_test):
    return


@pytest.fixture
def users() -> Generator[list[User]]:
    with db.begin():
        created = [
            db.create(
                User,
                Username=f"concurrent{i}",
                Email=f"concurrent{i}@example.invalid",
                RealName=f"Concurrent {i}",
                Passwd="testPassword",
                AccountTypeID=USER_ID,
            )
            for i in range(NUM_USERS)
        ]
    yield created


@pytest.mark.asyncio
async def test_concurrent_logins_do_not_crash(users: list[User]) -> None:
    headers = {"Referer": aurweb.config.get("options", "aur_location") + "/login"}

    # ASGITransport doesn't fire lifespan; drive it so routes get mounted.
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://test", follow_redirects=False
        ) as client:

            async def one_login(username: str) -> int:
                r = await client.post(
                    "/login",
                    data={"user": username, "passwd": "testPassword", "next": "/"},
                    headers=headers,
                )
                return r.status_code

            tasks = [
                one_login(u.Username) for u in users for _ in range(LOGINS_PER_USER)
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

    failures = [r for r in results if isinstance(r, Exception)]
    assert not failures, f"login raised: {failures[:3]}"
    bad = [r for r in results if r not in (200, 303)]
    assert not bad, f"unexpected codes: {sorted(set(bad))}"
