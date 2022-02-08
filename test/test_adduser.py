from typing import List
from unittest import mock

import pytest

import aurweb.models.account_type as at

from aurweb import db
from aurweb.models import User
from aurweb.scripts import adduser
from aurweb.testing.requests import Request

TEST_SSH_PUBKEY = ("ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAI"
                   "bmlzdHAyNTYAAABBBEURnkiY6JoLyqDE8Li1XuAW+LHmkmLDMW/GL5wY"
                   "7k4/A+Ta7bjA3MOKrF9j4EuUTvCuNXULxvpfSqheTFWZc+g= "
                   "kevr@volcano")


@pytest.fixture(autouse=True)
def setup(db_test):
    return


def run_main(args: List[str] = []):
    with mock.patch("sys.argv", ["aurweb-adduser"] + args):
        adduser.main()


def test_adduser_no_args():
    with pytest.raises(SystemExit):
        run_main()


def test_adduser():
    run_main(["-u", "test", "-e", "test@example.org", "-p", "abcd1234"])
    test = db.query(User).filter(User.Username == "test").first()
    assert test is not None
    assert test.login(Request(), "abcd1234")


def test_adduser_tu():
    run_main([
        "-u", "test", "-e", "test@example.org", "-p", "abcd1234",
        "-t", at.TRUSTED_USER
    ])
    test = db.query(User).filter(User.Username == "test").first()
    assert test is not None
    assert test.AccountTypeID == at.TRUSTED_USER_ID


def test_adduser_ssh_pk():
    run_main(["-u", "test", "-e", "test@example.org", "-p", "abcd1234",
              "--ssh-pubkey", TEST_SSH_PUBKEY])
    test = db.query(User).filter(User.Username == "test").first()
    assert test is not None
    assert TEST_SSH_PUBKEY.startswith(test.ssh_pub_keys.first().PubKey)
