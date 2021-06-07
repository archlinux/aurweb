from sqlalchemy.ext.declarative import declarative_base

import aurweb.db

Base = declarative_base()
Base.__table_args__ = {
    "autoload": True,
    "autoload_with": aurweb.db.get_engine(),
    "extend_existing": True
}
