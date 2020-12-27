from fastapi import Request
from sqlalchemy.orm import mapper

from aurweb.schema import Bans


class Ban:
    def __init__(self, **kwargs):
        self.IPAddress = kwargs.get("IPAddress")
        self.BanTS = kwargs.get("BanTS")


def is_banned(request: Request):
    from aurweb.db import session
    ip = request.client.host
    return session.query(Ban).filter(Ban.IPAddress == ip).first() is not None


mapper(Ban, Bans)
