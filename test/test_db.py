import os
import re
import sqlite3
import tempfile

from unittest import mock

import mysql.connector
import pytest

import aurweb.config

from aurweb import db
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
    setup_test_db()


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


def make_temp_config(backend):
    if not os.path.isdir("/tmp"):
        os.mkdir("/tmp")
    tmpdir = tempfile.mkdtemp()
    tmp = os.path.join(tmpdir, "config.tmp")
    with open("conf/config") as f:
        config = re.sub(r'backend = sqlite', f'backend = {backend}', f.read())
        with open(tmp, "w") as o:
            o.write(config)
    return (tmpdir, tmp)


def test_sqlalchemy_unknown_backend():
    tmpdir, tmp = make_temp_config("blah")

    with mock.patch.dict(os.environ, {"AUR_CONFIG": tmp}):
        aurweb.config.rehash()
        with pytest.raises(ValueError):
            db.get_sqlalchemy_url()
    aurweb.config.rehash()

    os.remove(tmp)
    os.removedirs(tmpdir)


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
    tmpdir, tmp = make_temp_config("blah")

    with mock.patch.dict(os.environ, {"AUR_CONFIG": tmp}):
        aurweb.config.rehash()
        with pytest.raises(ValueError):
            db.Connection()
    aurweb.config.rehash()

    os.remove(tmp)
    os.removedirs(tmpdir)


@mock.patch("mysql.connector.connect", mock.MagicMock(return_value=True))
@mock.patch.object(mysql.connector, "paramstyle", "qmark")
def test_connection_mysql():
    tmpdir, tmp = make_temp_config("mysql")
    with mock.patch.dict(os.environ, {
        "AUR_CONFIG": tmp,
        "AUR_CONFIG_DEFAULTS": "conf/config.defaults"
    }):
        aurweb.config.rehash()
        db.Connection()
    aurweb.config.rehash()

    os.remove(tmp)
    os.removedirs(tmpdir)


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
