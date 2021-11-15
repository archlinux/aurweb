from fastapi import Request

from aurweb import db, schema
from aurweb.models.declarative import Base


class Ban(Base):
    __table__ = schema.Bans
    __tablename__ = __table__.name
    __mapper_args__ = {"primary_key": [__table__.c.IPAddress]}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


def is_banned(request: Request):
    ip = request.client.host
    exists = db.query(Ban).filter(Ban.IPAddress == ip).exists()
    return db.query(exists).scalar()
