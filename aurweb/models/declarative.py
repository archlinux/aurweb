import json

from sqlalchemy.ext.declarative import declarative_base

from aurweb import util


def to_dict(model):
    return {
        c.name: getattr(model, c.name)
        for c in model.__table__.columns
    }


def to_json(model, indent: int = None):
    return json.dumps({
        k: util.jsonify(v)
        for k, v in to_dict(model).items()
    }, indent=indent)


Base = declarative_base()

# Setup __table_args__ applicable to every table.
Base.__table_args__ = {
    "autoload": False,
    "extend_existing": True
}

# Setup Base.as_dict and Base.json.
#
# With this, declarative models can use .as_dict() or .json()
# at any time to produce a dict and json out of table columns.
#
Base.as_dict = to_dict
Base.json = to_json
