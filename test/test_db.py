import os
import re
import sqlite3
import tempfile

from unittest import mock

import pytest

import aurweb.config
import aurweb.initdb

from aurweb import db
from aurweb.models.account_type import AccountType
from aurweb.testing import setup_test_db


class Args:
    """ Stub arguments used for running aurweb.initdb. """
    use_alembic = True
    verbose = True


class DBCursor:
    """ A fake database cursor object used in tests. """
    items = []

    def execute(self, *args, **kwargs):
        self.items = list(args)
        return self

    def fetchall(self):
        return self.items


class DBConnection:
    """ A fake database connection object used in tests. """
    @staticmethod
    def cursor():
        return DBCursor()

    @staticmethod
    def create_function(name, num_args, func):
        pass


def make_temp_config(config_file, *replacements):
    """ Generate a temporary config file with a set of replacements.

    :param *replacements: A variable number of tuple regex replacement pairs
    :return: A tuple containing (temp directory, temp config file)
    """
    tmpdir = tempfile.TemporaryDirectory()
    tmp = os.path.join(tmpdir.name, "config.tmp")
    with open(config_file) as f:
        config = f.read()
        for repl in list(replacements):
            config = re.sub(repl[0], repl[1], config)
        with open(tmp, "w") as o:
            o.write(config)
        aurwebdir = aurweb.config.get("options", "aurwebdir")
        defaults = os.path.join(aurwebdir, "conf/config.defaults")
        with open(defaults) as i:
            with open(f"{tmp}.defaults", "w") as o:
                o.write(i.read())
    return tmpdir, tmp


def make_temp_sqlite_config(config_file):
    return make_temp_config(config_file,
                            (r"backend = .*", "backend = sqlite"),
                            (r"name = .*", "name = /tmp/aurweb.sqlite3"))


def make_temp_mysql_config(config_file):
    return make_temp_config(config_file,
                            (r"backend = .*", "backend = mysql"),
                            (r"name = .*", "name = aurweb"))


@pytest.fixture(autouse=True)
def setup_db():
    if os.path.exists("/tmp/aurweb.sqlite3"):
        os.remove("/tmp/aurweb.sqlite3")

    # In various places in this test, we reinitialize the engine.
    # Make sure we kill the previous engine before initializing
    # it via setup_test_db().
    aurweb.db.kill_engine()
    setup_test_db()


def test_sqlalchemy_sqlite_url():
    tmpctx, tmp = make_temp_sqlite_config("conf/config")
    with tmpctx:
        with mock.patch.dict(os.environ, {"AUR_CONFIG": tmp}):
            aurweb.config.rehash()
            assert db.get_sqlalchemy_url()
    aurweb.config.rehash()


def test_sqlalchemy_mysql_url():
    tmpctx, tmp = make_temp_mysql_config("conf/config")
    with tmpctx:
        with mock.patch.dict(os.environ, {"AUR_CONFIG": tmp}):
            aurweb.config.rehash()
            assert db.get_sqlalchemy_url()
    aurweb.config.rehash()


def test_sqlalchemy_mysql_port_url():
    tmpctx, tmp = make_temp_config("conf/config",
                                   (r";port = 3306", "port = 3306"))

    with tmpctx:
        with mock.patch.dict(os.environ, {"AUR_CONFIG": tmp}):
            aurweb.config.rehash()
            assert db.get_sqlalchemy_url()
        aurweb.config.rehash()


def test_sqlalchemy_unknown_backend():
    tmpctx, tmp = make_temp_config("conf/config",
                                   (r"backend = mysql", "backend = blah"))

    with tmpctx:
        with mock.patch.dict(os.environ, {"AUR_CONFIG": tmp}):
            aurweb.config.rehash()
            with pytest.raises(ValueError):
                db.get_sqlalchemy_url()
        aurweb.config.rehash()


def test_db_connects_without_fail():
    """ This only tests the actual config supplied to pytest. """
    db.connect()
    assert db.engine is not None


def test_connection_class_sqlite_without_fail():
    tmpctx, tmp = make_temp_sqlite_config("conf/config")
    with tmpctx:
        with mock.patch.dict(os.environ, {"AUR_CONFIG": tmp}):
            aurweb.config.rehash()

            aurweb.db.kill_engine()
            aurweb.initdb.run(Args())

            conn = db.Connection()
            cur = conn.execute(
                "SELECT AccountType FROM AccountTypes WHERE ID = ?", (1,))
            account_type = cur.fetchone()[0]
            assert account_type == "User"
        aurweb.config.rehash()


def test_connection_class_unsupported_backend():
    tmpctx, tmp = make_temp_config("conf/config",
                                   (r"backend = mysql", "backend = blah"))

    with tmpctx:
        with mock.patch.dict(os.environ, {"AUR_CONFIG": tmp}):
            aurweb.config.rehash()
            with pytest.raises(ValueError):
                db.Connection()
        aurweb.config.rehash()


@mock.patch("MySQLdb.connect", mock.MagicMock(return_value=True))
def test_connection_mysql():
    tmpctx, tmp = make_temp_mysql_config("conf/config")
    with tmpctx:
        with mock.patch.dict(os.environ, {
            "AUR_CONFIG": tmp,
            "AUR_CONFIG_DEFAULTS": "conf/config.defaults"
        }):
            aurweb.config.rehash()
            db.Connection()
        aurweb.config.rehash()


@mock.patch("sqlite3.connect", mock.MagicMock(return_value=DBConnection()))
@mock.patch.object(sqlite3, "paramstyle", "qmark")
def test_connection_sqlite():
    db.Connection()


@mock.patch("sqlite3.connect", mock.MagicMock(return_value=DBConnection()))
@mock.patch.object(sqlite3, "paramstyle", "format")
def test_connection_execute_paramstyle_format():
    tmpctx, tmp = make_temp_sqlite_config("conf/config")

    with tmpctx:
        with mock.patch.dict(os.environ, {
            "AUR_CONFIG": tmp,
            "AUR_CONFIG_DEFAULTS": "conf/config.defaults"
        }):
            aurweb.config.rehash()

            aurweb.db.kill_engine()
            aurweb.initdb.run(Args())

            # Test SQLite route of clearing tables.
            setup_test_db("Users", "Bans")

            conn = db.Connection()

            # First, test ? to %s format replacement.
            account_types = conn\
                .execute("SELECT * FROM AccountTypes WHERE AccountType = ?",
                         ["User"]).fetchall()
            assert account_types == \
                ["SELECT * FROM AccountTypes WHERE AccountType = %s", ["User"]]

            # Test other format replacement.
            account_types = conn\
                .execute("SELECT * FROM AccountTypes WHERE AccountType = %",
                         ["User"]).fetchall()
            assert account_types == \
                ["SELECT * FROM AccountTypes WHERE AccountType = %%", ["User"]]
        aurweb.config.rehash()


@mock.patch("sqlite3.connect", mock.MagicMock(return_value=DBConnection()))
@mock.patch.object(sqlite3, "paramstyle", "qmark")
def test_connection_execute_paramstyle_qmark():
    tmpctx, tmp = make_temp_sqlite_config("conf/config")

    with tmpctx:
        with mock.patch.dict(os.environ, {
            "AUR_CONFIG": tmp,
            "AUR_CONFIG_DEFAULTS": "conf/config.defaults"
        }):
            aurweb.config.rehash()

            aurweb.db.kill_engine()
            aurweb.initdb.run(Args())

            conn = db.Connection()
            # We don't modify anything when using qmark, so test equality.
            account_types = conn\
                .execute("SELECT * FROM AccountTypes WHERE AccountType = ?",
                         ["User"]).fetchall()
            assert account_types == \
                ["SELECT * FROM AccountTypes WHERE AccountType = ?", ["User"]]
        aurweb.config.rehash()


@mock.patch("sqlite3.connect", mock.MagicMock(return_value=DBConnection()))
@mock.patch.object(sqlite3, "paramstyle", "unsupported")
def test_connection_execute_paramstyle_unsupported():
    tmpctx, tmp = make_temp_sqlite_config("conf/config")
    with tmpctx:
        with mock.patch.dict(os.environ, {
            "AUR_CONFIG": tmp,
            "AUR_CONFIG_DEFAULTS": "conf/config.defaults"
        }):
            aurweb.config.rehash()
            conn = db.Connection()
            with pytest.raises(ValueError, match="unsupported paramstyle"):
                conn.execute(
                    "SELECT * FROM AccountTypes WHERE AccountType = ?",
                    ["User"]
                ).fetchall()
        aurweb.config.rehash()


def test_create_delete():
    db.create(AccountType, AccountType="test")
    record = db.query(AccountType, AccountType.AccountType == "test").first()
    assert record is not None
    db.delete(AccountType, AccountType.AccountType == "test")
    record = db.query(AccountType, AccountType.AccountType == "test").first()
    assert record is None

    # Create and delete a record with autocommit=False.
    db.create(AccountType, AccountType="test", autocommit=False)
    db.commit()
    db.delete(AccountType, AccountType.AccountType == "test", autocommit=False)
    db.commit()
    record = db.query(AccountType, AccountType.AccountType == "test").first()
    assert record is None


def test_add_commit():
    # Use db.add and db.commit to add a temporary record.
    account_type = AccountType(AccountType="test")
    db.add(account_type)
    db.commit()

    # Assert it got created in the DB.
    assert bool(account_type.ID)

    # Query the DB for it and compare the record with our object.
    record = db.query(AccountType, AccountType.AccountType == "test").first()
    assert record == account_type

    # Remove the record.
    db.delete(AccountType, AccountType.ID == account_type.ID)


def test_connection_executor_mysql_paramstyle():
    executor = db.ConnectionExecutor(None, backend="mysql")
    assert executor.paramstyle() == "format"


@mock.patch("sqlite3.paramstyle", "pyformat")
def test_connection_executor_sqlite_paramstyle():
    executor = db.ConnectionExecutor(None, backend="sqlite")
    assert executor.paramstyle() == sqlite3.paramstyle
