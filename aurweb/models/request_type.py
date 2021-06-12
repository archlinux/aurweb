from sqlalchemy import Column, Integer

from aurweb.models.declarative import Base


class RequestType(Base):
    __tablename__ = "RequestTypes"

    ID = Column(Integer, primary_key=True)

    __mapper_args__ = {"primary_key": [ID]}
