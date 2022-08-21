import pytest

import aurweb.config
import aurweb.db
import aurweb.initdb
from aurweb.models.account_type import AccountType


@pytest.fixture(autouse=True)
def setup(db_test):
    return


class Args:
    use_alembic = True
    verbose = True


def test_run():
    from aurweb.schema import metadata

    aurweb.db.kill_engine()
    metadata.drop_all(aurweb.db.get_engine())
    aurweb.initdb.run(Args())

    # Check that constant table rows got added via initdb.
    record = aurweb.db.query(AccountType, AccountType.AccountType == "User").first()
    assert record is not None
