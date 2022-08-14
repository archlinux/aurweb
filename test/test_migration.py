import pytest

from sqlalchemy import inspect

from aurweb.db import get_engine
from aurweb.models.ssh_pub_key import SSHPubKey


@pytest.fixture(autouse=True)
def setup(db_test):
    return


def test_sshpubkeys_pubkey_index():
    insp = inspect(get_engine())
    indexes = insp.get_indexes(SSHPubKey.__tablename__)

    found_pk = False
    for idx in indexes:
        if idx.get("name") == "SSHPubKeysPubKey":
            assert idx.get("column_names") == ["PubKey"]
            found_pk = True
    assert found_pk
