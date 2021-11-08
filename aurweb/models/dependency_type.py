from aurweb import schema
from aurweb.models.declarative import Base

DEPENDS = "depends"
MAKEDEPENDS = "makedepends"
CHECKDEPENDS = "checkdepends"
OPTDEPENDS = "optdepends"

DEPENDS_ID = 1
MAKEDEPENDS_ID = 2
CHECKDEPENDS_ID = 3
OPTDEPENDS_ID = 4


class DependencyType(Base):
    __table__ = schema.DependencyTypes
    __tablename__ = __table__.name
    __mapper_args__ = {"primary_key": [__table__.c.ID]}

    def __init__(self, Name: str = None):
        self.Name = Name
