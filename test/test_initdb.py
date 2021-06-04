import aurweb.config
import aurweb.db
import aurweb.initdb

from aurweb.models.account_type import AccountType


class Args:
    use_alembic = True
    verbose = True


def test_run():
    from aurweb.schema import metadata
    aurweb.db.kill_engine()
    metadata.drop_all(aurweb.db.get_engine())
    aurweb.initdb.run(Args())
    record = aurweb.db.query(AccountType,
                             AccountType.AccountType == "User").first()
    assert record is not None
