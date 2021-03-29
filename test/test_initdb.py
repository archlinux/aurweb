import pytest

import aurweb.config
import aurweb.db
import aurweb.initdb

from aurweb.models.account_type import AccountType
from aurweb.schema import metadata
from aurweb.testing import setup_test_db


@pytest.fixture(autouse=True)
def setup():
    setup_test_db()

    tables = metadata.tables.keys()
    for table in tables:
        aurweb.db.session.execute(f"DROP TABLE IF EXISTS {table}")


def test_run():
    class Args:
        use_alembic = True
        verbose = False
    aurweb.initdb.run(Args())
    assert aurweb.db.session.query(AccountType).filter(
        AccountType.AccountType == "User").first() is not None
