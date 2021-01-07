import os
import re
import sqlite3
import tempfile

from unittest import mock

import mysql.connector
import pytest

import aurweb.config

from aurweb import db
from aurweb.models.account_type import AccountType
from aurweb.testing import setup_test_db


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


@pytest.fixture(autouse=True)
def setup_db():
    setup_test_db("Bans")


def test_sqlalchemy_sqlite_url():
    with mock.patch.dict(os.environ, {"AUR_CONFIG": "conf/config.dev"}):
        aurweb.config.rehash()
        assert db.get_sqlalchemy_url()
    aurweb.config.rehash()


def test_sqlalchemy_mysql_url():
    with mock.patch.dict(os.environ, {"AUR_CONFIG": "conf/config.defaults"}):
        aurweb.config.rehash()
        assert db.get_sqlalchemy_url()
    aurweb.config.rehash()


def test_sqlalchemy_mysql_port_url():
    tmpctx, tmp = make_temp_config("conf/config.defaults", ";port = 3306", "port = 3306")

    with tmpctx:
        with mock.patch.dict(os.environ, {"AUR_CONFIG": tmp}):
            aurweb.config.rehash()
            assert db.get_sqlalchemy_url()
        aurweb.config.rehash()


def make_temp_config(config_file, src_str, replace_with):
    tmpdir = tempfile.TemporaryDirectory()
    tmp = os.path.join(tmpdir.name, "config.tmp")
    with open(config_file) as f:
        config = re.sub(src_str, f'{replace_with}', f.read())
        with open(tmp, "w") as o:
            o.write(config)
    return tmpdir, tmp


def test_sqlalchemy_unknown_backend():
    tmpctx, tmp = make_temp_config("conf/config", "backend = sqlite", "backend = blah")

    with tmpctx:
        with mock.patch.dict(os.environ, {"AUR_CONFIG": tmp}):
            aurweb.config.rehash()
            with pytest.raises(ValueError):
                db.get_sqlalchemy_url()
        aurweb.config.rehash()


def test_db_connects_without_fail():
    db.connect()
    assert db.engine is not None


def test_connection_class_without_fail():
    conn = db.Connection()

    cur = conn.execute(
        "SELECT AccountType FROM AccountTypes WHERE ID = ?", (1,))
    account_type = cur.fetchone()[0]

    assert account_type == "User"


def test_connection_class_unsupported_backend():
    tmpctx, tmp = make_temp_config("conf/config", "backend = sqlite", "backend = blah")

    with tmpctx:
        with mock.patch.dict(os.environ, {"AUR_CONFIG": tmp}):
            aurweb.config.rehash()
            with pytest.raises(ValueError):
                db.Connection()
        aurweb.config.rehash()


@mock.patch("mysql.connector.connect", mock.MagicMock(return_value=True))
@mock.patch.object(mysql.connector, "paramstyle", "qmark")
def test_connection_mysql():
    tmpctx, tmp = make_temp_config("conf/config", "backend = sqlite", "backend = mysql")
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
    conn = db.Connection()

    # First, test ? to %s format replacement.
    account_types = conn\
        .execute("SELECT * FROM AccountTypes WHERE AccountType = ?", ["User"])\
        .fetchall()
    assert account_types == \
        ["SELECT * FROM AccountTypes WHERE AccountType = %s", ["User"]]

    # Test other format replacement.
    account_types = conn\
        .execute("SELECT * FROM AccountTypes WHERE AccountType = %", ["User"])\
        .fetchall()
    assert account_types == \
        ["SELECT * FROM AccountTypes WHERE AccountType = %%", ["User"]]


@mock.patch("sqlite3.connect", mock.MagicMock(return_value=DBConnection()))
@mock.patch.object(sqlite3, "paramstyle", "qmark")
def test_connection_execute_paramstyle_qmark():
    conn = db.Connection()
    # We don't modify anything when using qmark, so test equality.
    account_types = conn\
        .execute("SELECT * FROM AccountTypes WHERE AccountType = ?", ["User"])\
        .fetchall()
    assert account_types == \
        ["SELECT * FROM AccountTypes WHERE AccountType = ?", ["User"]]


@mock.patch("sqlite3.connect", mock.MagicMock(return_value=DBConnection()))
@mock.patch.object(sqlite3, "paramstyle", "unsupported")
def test_connection_execute_paramstyle_unsupported():
    conn = db.Connection()
    with pytest.raises(ValueError, match="unsupported paramstyle"):
        conn.execute(
            "SELECT * FROM AccountTypes WHERE AccountType = ?",
            ["User"]
        ).fetchall()


def test_create_delete():
    db.create(AccountType, AccountType="test")
    record = db.query(AccountType, AccountType.AccountType == "test").first()
    assert record is not None
    db.delete(AccountType, AccountType.AccountType == "test")
    record = db.query(AccountType, AccountType.AccountType == "test").first()
    assert record is None


@mock.patch("mysql.connector.paramstyle", "qmark")
def test_connection_executor_mysql_paramstyle():
    executor = db.ConnectionExecutor(None, backend="mysql")
    assert executor.paramstyle() == "qmark"


@mock.patch("sqlite3.paramstyle", "pyformat")
def test_connection_executor_sqlite_paramstyle():
    executor = db.ConnectionExecutor(None, backend="sqlite")
    assert executor.paramstyle() == "pyformat"
