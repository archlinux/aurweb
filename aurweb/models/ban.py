from fastapi import Request
from sqlalchemy import Column, String

from aurweb.models.declarative import Base


class Ban(Base):
    __tablename__ = "Bans"

    IPAddress = Column(String(45), primary_key=True)

    __mapper_args__ = {"primary_key": [IPAddress]}

    def __init__(self, **kwargs):
        self.IPAddress = kwargs.get("IPAddress")
        self.BanTS = kwargs.get("BanTS")


def is_banned(request: Request):
    from aurweb.db import session
    ip = request.client.host
    return session.query(Ban).filter(Ban.IPAddress == ip).first() is not None
