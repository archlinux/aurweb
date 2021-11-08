from fastapi import Request

from aurweb import schema
from aurweb.models.declarative import Base


class Ban(Base):
    __table__ = schema.Bans
    __tablename__ = __table__.name
    __mapper_args__ = {"primary_key": [__table__.c.IPAddress]}

    def __init__(self, **kwargs):
        self.IPAddress = kwargs.get("IPAddress")
        self.BanTS = kwargs.get("BanTS")


def is_banned(request: Request):
    from aurweb.db import session
    ip = request.client.host
    return session.query(Ban).filter(Ban.IPAddress == ip).first() is not None
