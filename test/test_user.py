import hashlib
import json

from datetime import datetime, timedelta

import bcrypt
import pytest

import aurweb.auth
import aurweb.config

from aurweb import db
from aurweb.models.account_type import AccountType
from aurweb.models.ban import Ban
from aurweb.models.package import Package
from aurweb.models.package_base import PackageBase
from aurweb.models.package_notification import PackageNotification
from aurweb.models.package_vote import PackageVote
from aurweb.models.session import Session
from aurweb.models.ssh_pub_key import SSHPubKey
from aurweb.models.user import User
from aurweb.testing import setup_test_db
from aurweb.testing.requests import Request

account_type = user = None


@pytest.fixture(autouse=True)
def setup():
    global account_type, user

    setup_test_db(
        User.__tablename__,
        Session.__tablename__,
        Ban.__tablename__,
        SSHPubKey.__tablename__,
        Package.__tablename__,
        PackageBase.__tablename__,
        PackageVote.__tablename__,
        PackageNotification.__tablename__
    )

    account_type = db.query(AccountType,
                            AccountType.AccountType == "User").first()

    with db.begin():
        user = db.create(User, Username="test", Email="test@example.org",
                         RealName="Test User", Passwd="testPassword",
                         AccountType=account_type)


def test_user_login_logout():
    """ Test creating a user and reading its columns. """
    # Assert that make_user created a valid user.
    assert bool(user.ID)

    # Test authentication.
    assert user.valid_password("testPassword")
    assert not user.valid_password("badPassword")

    assert user in account_type.users

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

    # Ensure we've got the correct account type.
    assert user.AccountType.ID == account_type.ID
    assert user.AccountType.AccountType == account_type.AccountType

    # Test out user string functions.
    assert repr(user) == f"<User(ID='{user.ID}', " + \
        "AccountType='User', Username='test')>"

    # Test logout.
    user.logout(request)
    assert "AURSID" not in request.cookies
    assert not user.is_authenticated()


def test_user_login_twice():
    request = Request()
    assert user.login(request, "testPassword")
    assert user.login(request, "testPassword")


def test_user_login_banned():
    # Add ban for the next 30 seconds.
    banned_timestamp = datetime.utcnow() + timedelta(seconds=30)
    with db.begin():
        db.create(Ban, IPAddress="127.0.0.1", BanTS=banned_timestamp)

    request = Request()
    request.client.host = "127.0.0.1"
    assert not user.login(request, "testPassword")


def test_user_login_suspended():
    with db.begin():
        user.Suspended = True
    assert not user.login(Request(), "testPassword")


def test_legacy_user_authentication():
    with db.begin():
        user.Salt = bcrypt.gensalt().decode()
        user.Passwd = hashlib.md5(
            f"{user.Salt}testPassword".encode()
        ).hexdigest()

    assert not user.valid_password("badPassword")
    assert user.valid_password("testPassword")

    # Test by passing a password of None value in.
    assert not user.valid_password(None)


def test_user_login_with_outdated_sid():
    # Make a session with a LastUpdateTS 5 seconds ago, causing
    # user.login to update it with a new sid.
    with db.begin():
        db.create(Session, UsersID=user.ID, SessionID="stub",
                  LastUpdateTS=datetime.utcnow().timestamp() - 5)
    sid = user.login(Request(), "testPassword")
    assert sid and user.is_authenticated()
    assert sid != "stub"


def test_user_update_password():
    user.update_password("secondPassword")
    assert not user.valid_password("testPassword")
    assert user.valid_password("secondPassword")


def test_user_minimum_passwd_length():
    passwd_min_len = aurweb.config.getint("options", "passwd_min_len")
    assert User.minimum_passwd_length() == passwd_min_len


def test_user_has_credential():
    assert user.has_credential("CRED_PKGBASE_FLAG")
    assert not user.has_credential("CRED_ACCOUNT_CHANGE_TYPE")


def test_user_ssh_pub_key():
    assert user.ssh_pub_key is None

    with db.begin():
        ssh_pub_key = db.create(SSHPubKey, UserID=user.ID,
                                Fingerprint="testFingerprint",
                                PubKey="testPubKey")

    assert user.ssh_pub_key == ssh_pub_key


def test_user_credential_types():
    assert aurweb.auth.user_developer_or_trusted_user(user)
    assert not aurweb.auth.trusted_user(user)
    assert not aurweb.auth.developer(user)
    assert not aurweb.auth.trusted_user_or_dev(user)

    trusted_user_type = db.query(AccountType).filter(
        AccountType.AccountType == "Trusted User"
    ).first()
    with db.begin():
        user.AccountType = trusted_user_type

    assert aurweb.auth.trusted_user(user)
    assert aurweb.auth.trusted_user_or_dev(user)

    developer_type = db.query(AccountType,
                              AccountType.AccountType == "Developer").first()
    with db.begin():
        user.AccountType = developer_type

    assert aurweb.auth.developer(user)
    assert aurweb.auth.trusted_user_or_dev(user)

    type_str = "Trusted User & Developer"
    elevated_type = db.query(AccountType,
                             AccountType.AccountType == type_str).first()
    with db.begin():
        user.AccountType = elevated_type

    assert aurweb.auth.trusted_user(user)
    assert aurweb.auth.developer(user)
    assert aurweb.auth.trusted_user_or_dev(user)


def test_user_json():
    data = json.loads(user.json())
    assert data.get("ID") == user.ID
    assert data.get("Username") == user.Username
    assert data.get("Email") == user.Email
    # .json() converts datetime values to integer timestamps.
    assert isinstance(data.get("RegistrationTS"), int)


def test_user_as_dict():
    data = user.as_dict()
    assert data.get("ID") == user.ID
    assert data.get("Username") == user.Username
    assert data.get("Email") == user.Email
    # .as_dict() does not convert values to json-capable types.
    assert isinstance(data.get("RegistrationTS"), datetime)


def test_user_is_trusted_user():
    tu_type = db.query(AccountType,
                       AccountType.AccountType == "Trusted User").first()
    with db.begin():
        user.AccountType = tu_type
    assert user.is_trusted_user() is True

    # Do it again with the combined role.
    tu_type = db.query(
        AccountType,
        AccountType.AccountType == "Trusted User & Developer").first()
    with db.begin():
        user.AccountType = tu_type
    assert user.is_trusted_user() is True


def test_user_is_developer():
    dev_type = db.query(AccountType,
                        AccountType.AccountType == "Developer").first()
    with db.begin():
        user.AccountType = dev_type
    assert user.is_developer() is True

    # Do it again with the combined role.
    dev_type = db.query(
        AccountType,
        AccountType.AccountType == "Trusted User & Developer").first()
    with db.begin():
        user.AccountType = dev_type
    assert user.is_developer() is True


def test_user_voted_for():
    now = int(datetime.utcnow().timestamp())
    with db.begin():
        pkgbase = db.create(PackageBase, Name="pkg1", Maintainer=user)
        pkg = db.create(Package, PackageBase=pkgbase, Name=pkgbase.Name)
        db.create(PackageVote, PackageBase=pkgbase, User=user, VoteTS=now)
    assert user.voted_for(pkg)


def test_user_notified():
    with db.begin():
        pkgbase = db.create(PackageBase, Name="pkg1", Maintainer=user)
        pkg = db.create(Package, PackageBase=pkgbase, Name=pkgbase.Name)
        db.create(PackageNotification, PackageBase=pkgbase, User=user)
    assert user.notified(pkg)


def test_user_packages():
    with db.begin():
        pkgbase = db.create(PackageBase, Name="pkg1", Maintainer=user)
        pkg = db.create(Package, PackageBase=pkgbase, Name=pkgbase.Name)
    assert pkg in user.packages()
