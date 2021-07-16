from sqlalchemy import Column, Integer

from aurweb import db
from aurweb.models.declarative import Base

DEPENDS = "depends"
MAKEDEPENDS = "makedepends"
CHECKDEPENDS = "checkdepends"
OPTDEPENDS = "optdepends"


class DependencyType(Base):
    __tablename__ = "DependencyTypes"

    ID = Column(Integer, primary_key=True)

    __mapper_args__ = {"primary_key": [ID]}

    def __init__(self, Name: str = None):
        self.Name = Name


DEPENDS_ID = db.query(DependencyType).filter(
    DependencyType.Name == DEPENDS).first().ID
MAKEDEPENDS_ID = db.query(DependencyType).filter(
    DependencyType.Name == MAKEDEPENDS).first().ID
CHECKDEPENDS_ID = db.query(DependencyType).filter(
    DependencyType.Name == CHECKDEPENDS).first().ID
OPTDEPENDS_ID = db.query(DependencyType).filter(
    DependencyType.Name == OPTDEPENDS).first().ID
