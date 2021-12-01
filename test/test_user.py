import hashlib
import json

from datetime import datetime, timedelta

import bcrypt
import pytest

import aurweb.auth
import aurweb.config
import aurweb.models.account_type as at

from aurweb import db
from aurweb.auth import creds
from aurweb.models.ban import Ban
from aurweb.models.package import Package
from aurweb.models.package_base import PackageBase
from aurweb.models.package_notification import PackageNotification
from aurweb.models.package_vote import PackageVote
from aurweb.models.session import Session
from aurweb.models.ssh_pub_key import SSHPubKey
from aurweb.models.user import User
from aurweb.testing.requests import Request


@pytest.fixture(autouse=True)
def setup(db_test):
    return


@pytest.fixture
def user() -> User:
    with db.begin():
        user = db.create(User, Username="test", Email="test@example.org",
                         RealName="Test User", Passwd="testPassword",
                         AccountTypeID=at.USER_ID)
    yield user


@pytest.fixture
def package(user: User) -> Package:
    with db.begin():
        pkgbase = db.create(PackageBase, Name="pkg1", Maintainer=user)
        pkg = db.create(Package, PackageBase=pkgbase, Name=pkgbase.Name)
    yield pkg


def test_user_login_logout(user: User):
    """ Test creating a user and reading its columns. """
    # Assert that make_user created a valid user.
    assert bool(user.ID)

    # Test authentication.
    assert user.valid_password("testPassword")
    assert not user.valid_password("badPassword")

    # Make a raw request.
    request = Request()
    assert not user.login(request, "badPassword")
    assert not user.is_authenticated()

    sid = user.login(request, "testPassword")
    assert sid is not None
    assert user.is_authenticated()
    assert "AURSID" in request.cookies

    # Expect that User session relationships work right.
    user_session = db.query(Session,
                            Session.UsersID == user.ID).first()
    assert user_session == user.session
    assert user.session.SessionID == sid
    assert user.session.User == user

    # Search for the user via query API.
    result = db.query(User, User.ID == user.ID).first()

    # Compare the result and our original user.
    assert result == user
    assert result.ID == user.ID
    assert result.AccountType.ID == user.AccountType.ID
    assert result.Username == user.Username
    assert result.Email == user.Email

    # Test result authenticate methods to ensure they work the same.
    assert not result.valid_password("badPassword")
    assert result.valid_password("testPassword")
    assert result.is_authenticated()

    # Test out user string functions.
    assert repr(user) == f"<User(ID='{user.ID}', " + \
        "AccountType='User', Username='test')>"

    # Test logout.
    user.logout(request)
    assert "AURSID" not in request.cookies
    assert not user.is_authenticated()


def test_user_login_twice(user: User):
    request = Request()
    assert user.login(request, "testPassword")
    assert user.login(request, "testPassword")


def test_user_login_banned(user: User):
    # Add ban for the next 30 seconds.
    banned_timestamp = datetime.utcnow() + timedelta(seconds=30)
    with db.begin():
        db.create(Ban, IPAddress="127.0.0.1", BanTS=banned_timestamp)

    request = Request()
    request.client.host = "127.0.0.1"
    assert not user.login(request, "testPassword")


def test_user_login_suspended(user: User):
    with db.begin():
        user.Suspended = True
    assert not user.login(Request(), "testPassword")


def test_legacy_user_authentication(user: User):
    with db.begin():
        user.Salt = bcrypt.gensalt().decode()
        user.Passwd = hashlib.md5(
            f"{user.Salt}testPassword".encode()
        ).hexdigest()

    assert not user.valid_password("badPassword")
    assert user.valid_password("testPassword")

    # Test by passing a password of None value in.
    assert not user.valid_password(None)


def test_user_login_with_outdated_sid(user: User):
    # Make a session with a LastUpdateTS 5 seconds ago, causing
    # user.login to update it with a new sid.
    with db.begin():
        db.create(Session, UsersID=user.ID, SessionID="stub",
                  LastUpdateTS=datetime.utcnow().timestamp() - 5)
    sid = user.login(Request(), "testPassword")
    assert sid and user.is_authenticated()
    assert sid != "stub"


def test_user_update_password(user: User):
    user.update_password("secondPassword")
    assert not user.valid_password("testPassword")
    assert user.valid_password("secondPassword")


def test_user_minimum_passwd_length():
    passwd_min_len = aurweb.config.getint("options", "passwd_min_len")
    assert User.minimum_passwd_length() == passwd_min_len


def test_user_has_credential(user: User):
    assert not user.has_credential(creds.ACCOUNT_CHANGE_TYPE)


def test_user_ssh_pub_key(user: User):
    assert user.ssh_pub_key is None

    with db.begin():
        ssh_pub_key = db.create(SSHPubKey, UserID=user.ID,
                                Fingerprint="testFingerprint",
                                PubKey="testPubKey")

    assert user.ssh_pub_key == ssh_pub_key


def test_user_credential_types(user: User):
    assert user.AccountTypeID in creds.user_developer_or_trusted_user
    assert user.AccountTypeID not in creds.trusted_user
    assert user.AccountTypeID not in creds.developer
    assert user.AccountTypeID not in creds.trusted_user_or_dev

    with db.begin():
        user.AccountTypeID = at.TRUSTED_USER_ID

    assert user.AccountTypeID in creds.trusted_user
    assert user.AccountTypeID in creds.trusted_user_or_dev

    with db.begin():
        user.AccountTypeID = at.DEVELOPER_ID

    assert user.AccountTypeID in creds.developer
    assert user.AccountTypeID in creds.trusted_user_or_dev

    with db.begin():
        user.AccountTypeID = at.TRUSTED_USER_AND_DEV_ID

    assert user.AccountTypeID in creds.trusted_user
    assert user.AccountTypeID in creds.developer
    assert user.AccountTypeID in creds.trusted_user_or_dev

    # Some model authorization checks.
    assert user.is_elevated()
    assert user.is_trusted_user()
    assert user.is_developer()


def test_user_json(user: User):
    data = json.loads(user.json())
    assert data.get("ID") == user.ID
    assert data.get("Username") == user.Username
    assert data.get("Email") == user.Email
    # .json() converts datetime values to integer timestamps.
    assert isinstance(data.get("RegistrationTS"), int)


def test_user_as_dict(user: User):
    data = user.as_dict()
    assert data.get("ID") == user.ID
    assert data.get("Username") == user.Username
    assert data.get("Email") == user.Email
    # .as_dict() does not convert values to json-capable types.
    assert isinstance(data.get("RegistrationTS"), datetime)


def test_user_is_trusted_user(user: User):
    with db.begin():
        user.AccountTypeID = at.TRUSTED_USER_ID
    assert user.is_trusted_user() is True

    # Do it again with the combined role.
    with db.begin():
        user.AccountTypeID = at.TRUSTED_USER_AND_DEV_ID
    assert user.is_trusted_user() is True


def test_user_is_developer(user: User):
    with db.begin():
        user.AccountTypeID = at.DEVELOPER_ID
    assert user.is_developer() is True

    # Do it again with the combined role.
    with db.begin():
        user.AccountTypeID = at.TRUSTED_USER_AND_DEV_ID
    assert user.is_developer() is True


def test_user_voted_for(user: User, package: Package):
    pkgbase = package.PackageBase
    now = int(datetime.utcnow().timestamp())
    with db.begin():
        db.create(PackageVote, PackageBase=pkgbase, User=user, VoteTS=now)
    assert user.voted_for(package)


def test_user_notified(user: User, package: Package):
    pkgbase = package.PackageBase
    with db.begin():
        db.create(PackageNotification, PackageBase=pkgbase, User=user)
    assert user.notified(package)


def test_user_packages(user: User, package: Package):
    assert package in user.packages()
