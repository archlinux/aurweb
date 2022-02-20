import re
import tempfile

from datetime import datetime
from http import HTTPStatus
from logging import DEBUG
from subprocess import Popen

import lxml.html
import pytest

from fastapi.testclient import TestClient

import aurweb.models.account_type as at

from aurweb import captcha, db, logging, time
from aurweb.asgi import app
from aurweb.db import create, query
from aurweb.models.accepted_term import AcceptedTerm
from aurweb.models.account_type import (DEVELOPER_ID, TRUSTED_USER, TRUSTED_USER_AND_DEV_ID, TRUSTED_USER_ID, USER_ID,
                                        AccountType)
from aurweb.models.ban import Ban
from aurweb.models.session import Session
from aurweb.models.ssh_pub_key import SSHPubKey, get_fingerprint
from aurweb.models.term import Term
from aurweb.models.user import User
from aurweb.testing.html import get_errors
from aurweb.testing.requests import Request

logger = logging.get_logger(__name__)

# Some test global constants.
TEST_USERNAME = "test"
TEST_EMAIL = "test@example.org"


def make_ssh_pubkey():
    # Create a public key with ssh-keygen (this adds ssh-keygen as a
    # dependency to passing this test).
    with tempfile.TemporaryDirectory() as tmpdir:
        with open("/dev/null", "w") as null:
            proc = Popen(["ssh-keygen", "-f", f"{tmpdir}/test.ssh", "-N", ""],
                         stdout=null, stderr=null)
            proc.wait()
        assert proc.returncode == 0

        # Read in the public key, then delete the temp dir we made.
        return open(f"{tmpdir}/test.ssh.pub").read().rstrip()


@pytest.fixture(autouse=True)
def setup(db_test):
    return


@pytest.fixture
def client() -> TestClient:
    yield TestClient(app=app)


def create_user(username: str) -> User:
    email = f"{username}@example.org"
    user = create(User, Username=username, Email=email,
                  Passwd="testPassword",
                  AccountTypeID=USER_ID)
    return user


@pytest.fixture
def user() -> User:
    with db.begin():
        user = create_user(TEST_USERNAME)
    yield user


@pytest.fixture
def tu_user(user: User):
    with db.begin():
        user.AccountTypeID = TRUSTED_USER_AND_DEV_ID
    yield user


def test_get_passreset_authed_redirects(client: TestClient, user: User):
    sid = user.login(Request(), "testPassword")
    assert sid is not None

    with client as request:
        response = request.get("/passreset", cookies={"AURSID": sid},
                               allow_redirects=False)

    assert response.status_code == int(HTTPStatus.SEE_OTHER)
    assert response.headers.get("location") == "/"


def test_get_passreset(client: TestClient):
    with client as request:
        response = request.get("/passreset")
    assert response.status_code == int(HTTPStatus.OK)


def test_get_passreset_translation(client: TestClient):
    # Test that translation works; set it to de.
    with client as request:
        response = request.get("/passreset", cookies={"AURLANG": "de"})

    # The header title should be translated.
    assert "Passwort zurücksetzen" in response.text

    # The form input label should be translated.
    expected = "Benutzername oder primäre E-Mail-Adresse eingeben:"
    assert expected in response.text

    # And the button.
    assert "Weiter" in response.text

    # Restore english.
    with client as request:
        response = request.get("/passreset", cookies={"AURLANG": "en"})


def test_get_passreset_with_resetkey(client: TestClient):
    with client as request:
        response = request.get("/passreset", data={"resetkey": "abcd"})
    assert response.status_code == int(HTTPStatus.OK)


def test_post_passreset_authed_redirects(client: TestClient, user: User):
    sid = user.login(Request(), "testPassword")
    assert sid is not None

    with client as request:
        response = request.post("/passreset",
                                cookies={"AURSID": sid},
                                data={"user": "blah"},
                                allow_redirects=False)

    assert response.status_code == int(HTTPStatus.SEE_OTHER)
    assert response.headers.get("location") == "/"


def test_post_passreset_user(client: TestClient, user: User):
    # With username.
    with client as request:
        response = request.post("/passreset", data={"user": TEST_USERNAME})
    assert response.status_code == int(HTTPStatus.SEE_OTHER)
    assert response.headers.get("location") == "/passreset?step=confirm"

    # With e-mail.
    with client as request:
        response = request.post("/passreset", data={"user": TEST_EMAIL})
    assert response.status_code == int(HTTPStatus.SEE_OTHER)
    assert response.headers.get("location") == "/passreset?step=confirm"


def test_post_passreset_user_suspended(client: TestClient, user: User):
    with db.begin():
        user.Suspended = True

    with client as request:
        response = request.post("/passreset", data={"user": TEST_USERNAME})
    assert response.status_code == int(HTTPStatus.NOT_FOUND)
    errors = get_errors(response.text)
    expected = "Invalid e-mail."
    assert errors[0].text.strip() == expected


def test_post_passreset_resetkey(client: TestClient, user: User):
    with db.begin():
        user.session = Session(UsersID=user.ID, SessionID="blah",
                               LastUpdateTS=time.utcnow())

    # Prepare a password reset.
    with client as request:
        response = request.post("/passreset", data={"user": TEST_USERNAME})
    assert response.status_code == int(HTTPStatus.SEE_OTHER)
    assert response.headers.get("location") == "/passreset?step=confirm"

    # Now that we've prepared the password reset, prepare a POST
    # request with the user's ResetKey.
    resetkey = user.ResetKey
    post_data = {
        "user": TEST_USERNAME,
        "resetkey": resetkey,
        "password": "abcd1234",
        "confirm": "abcd1234"
    }

    with client as request:
        response = request.post("/passreset", data=post_data)
    assert response.status_code == int(HTTPStatus.SEE_OTHER)
    assert response.headers.get("location") == "/passreset?step=complete"


def make_resetkey(client: TestClient, user: User):
    with client as request:
        response = request.post("/passreset", data={"user": TEST_USERNAME})
        assert response.status_code == int(HTTPStatus.SEE_OTHER)
        assert response.headers.get("location") == "/passreset?step=confirm"
    return user.ResetKey


def make_passreset_data(user: User, resetkey: str):
    return {
        "user": user.Username,
        "resetkey": resetkey
    }


def test_post_passreset_error_invalid_email(client: TestClient, user: User):
    # First, test with a user that doesn't even exist.
    with client as request:
        response = request.post("/passreset", data={"user": "invalid"})
    assert response.status_code == int(HTTPStatus.NOT_FOUND)
    assert "Invalid e-mail." in response.text

    # Then, test with an invalid resetkey for a real user.
    _ = make_resetkey(client, user)
    post_data = make_passreset_data(user, "fake")
    post_data["password"] = "abcd1234"
    post_data["confirm"] = "abcd1234"

    with client as request:
        response = request.post("/passreset", data=post_data)
    assert response.status_code == int(HTTPStatus.NOT_FOUND)
    assert "Invalid e-mail." in response.text


def test_post_passreset_error_missing_field(client: TestClient, user: User):
    # Now that we've prepared the password reset, prepare a POST
    # request with the user's ResetKey.
    resetkey = make_resetkey(client, user)
    post_data = make_passreset_data(user, resetkey)

    with client as request:
        response = request.post("/passreset", data=post_data)

    assert response.status_code == int(HTTPStatus.BAD_REQUEST)

    error = "Missing a required field."
    assert error in response.content.decode("utf-8")


def test_post_passreset_error_password_mismatch(client: TestClient,
                                                user: User):
    resetkey = make_resetkey(client, user)
    post_data = make_passreset_data(user, resetkey)

    post_data["password"] = "abcd1234"
    post_data["confirm"] = "mismatched"

    with client as request:
        response = request.post("/passreset", data=post_data)

    assert response.status_code == int(HTTPStatus.BAD_REQUEST)

    error = "Password fields do not match."
    assert error in response.content.decode("utf-8")


def test_post_passreset_error_password_requirements(client: TestClient,
                                                    user: User):
    resetkey = make_resetkey(client, user)
    post_data = make_passreset_data(user, resetkey)

    passwd_min_len = User.minimum_passwd_length()
    assert passwd_min_len >= 4

    post_data["password"] = "x"
    post_data["confirm"] = "x"

    with client as request:
        response = request.post("/passreset", data=post_data)

    assert response.status_code == int(HTTPStatus.BAD_REQUEST)

    error = f"Your password must be at least {passwd_min_len} characters."
    assert error in response.content.decode("utf-8")


def test_get_register(client: TestClient):
    with client as request:
        response = request.get("/register")
    assert response.status_code == int(HTTPStatus.OK)


def post_register(request, **kwargs):
    """ A simple helper that allows overrides to test defaults. """
    salt = captcha.get_captcha_salts()[0]
    token = captcha.get_captcha_token(salt)
    answer = captcha.get_captcha_answer(token)

    data = {
        "U": "newUser",
        "E": "newUser@email.org",
        "P": "newUserPassword",
        "C": "newUserPassword",
        "L": "en",
        "TZ": "UTC",
        "captcha": answer,
        "captcha_salt": salt
    }

    # For any kwargs given, override their k:v pairs in data.
    args = dict(kwargs)
    for k, v in args.items():
        data[k] = v

    return request.post("/register", data=data, allow_redirects=False)


def test_post_register(client: TestClient):
    with client as request:
        response = post_register(request)
    assert response.status_code == int(HTTPStatus.OK)

    expected = "The account, <strong>'newUser'</strong>, "
    expected += "has been successfully created."
    assert expected in response.content.decode()


def test_post_register_rejects_case_insensitive_spoof(client: TestClient):
    with client as request:
        response = post_register(request, U="newUser", E="newUser@example.org")
    assert response.status_code == int(HTTPStatus.OK)

    with client as request:
        response = post_register(request, U="NEWUSER", E="BLAH@GMAIL.COM")
    assert response.status_code == int(HTTPStatus.BAD_REQUEST)

    expected = "The username, <strong>NEWUSER</strong>, is already in use."
    assert expected in response.content.decode()

    with client as request:
        response = post_register(request, U="BLAH", E="NEWUSER@EXAMPLE.ORG")
    assert response.status_code == int(HTTPStatus.BAD_REQUEST)

    expected = "The address, <strong>NEWUSER@EXAMPLE.ORG</strong>, "
    expected += "is already in use."
    assert expected in response.content.decode()


def test_post_register_error_expired_captcha(client: TestClient):
    with client as request:
        response = post_register(request, captcha_salt="invalid-salt")

    assert response.status_code == int(HTTPStatus.BAD_REQUEST)

    content = response.content.decode()
    assert "This CAPTCHA has expired. Please try again." in content


def test_post_register_error_missing_captcha(client: TestClient):
    with client as request:
        response = post_register(request, captcha=None)

    assert response.status_code == int(HTTPStatus.BAD_REQUEST)

    content = response.content.decode()
    assert "The CAPTCHA is missing." in content


def test_post_register_error_invalid_captcha(client: TestClient):
    with client as request:
        response = post_register(request, captcha="invalid blah blah")

    assert response.status_code == int(HTTPStatus.BAD_REQUEST)

    content = response.content.decode()
    assert "The entered CAPTCHA answer is invalid." in content


def test_post_register_error_ip_banned(client: TestClient):
    # 'testclient' is used as request.client.host via FastAPI TestClient.
    with db.begin():
        create(Ban, IPAddress="testclient", BanTS=datetime.utcnow())

    with client as request:
        response = post_register(request)

    assert response.status_code == int(HTTPStatus.BAD_REQUEST)

    content = response.content.decode()
    assert ("Account registration has been disabled for your IP address, " +
            "probably due to sustained spam attacks. Sorry for the " +
            "inconvenience.") in content


def test_post_register_error_missing_username(client: TestClient):
    with client as request:
        response = post_register(request, U="")

    assert response.status_code == int(HTTPStatus.BAD_REQUEST)

    content = response.content.decode()
    assert "Missing a required field." in content


def test_post_register_error_missing_email(client: TestClient):
    with client as request:
        response = post_register(request, E="")

    assert response.status_code == int(HTTPStatus.BAD_REQUEST)

    content = response.content.decode()
    assert "Missing a required field." in content


def test_post_register_error_invalid_username(client: TestClient):
    with client as request:
        # Our test config requires at least three characters for a
        # valid username, so test against two characters: 'ba'.
        response = post_register(request, U="ba")

    assert response.status_code == int(HTTPStatus.BAD_REQUEST)

    content = response.content.decode()
    assert "The username is invalid." in content


def test_post_register_invalid_password(client: TestClient):
    with client as request:
        response = post_register(request, P="abc", C="abc")

    assert response.status_code == int(HTTPStatus.BAD_REQUEST)

    content = response.content.decode()
    expected = r"Your password must be at least \d+ characters."
    assert re.search(expected, content)


def test_post_register_error_missing_confirm(client: TestClient):
    with client as request:
        response = post_register(request, C=None)

    assert response.status_code == int(HTTPStatus.BAD_REQUEST)

    content = response.content.decode()
    assert "Please confirm your new password." in content


def test_post_register_error_mismatched_confirm(client: TestClient):
    with client as request:
        response = post_register(request, C="mismatched")

    assert response.status_code == int(HTTPStatus.BAD_REQUEST)

    content = response.content.decode()
    assert "Password fields do not match." in content


def test_post_register_error_invalid_email(client: TestClient):
    with client as request:
        response = post_register(request, E="bad@email")

    assert response.status_code == int(HTTPStatus.BAD_REQUEST)

    content = response.content.decode()
    assert "The email address is invalid." in content


def test_post_register_invalid_backup_email(client: TestClient):
    with client as request:
        response = post_register(request, BE="bad@email")

    assert response.status_code == int(HTTPStatus.BAD_REQUEST)

    content = response.content.decode()
    assert "The backup email address is invalid." in content


def test_post_register_error_invalid_homepage(client: TestClient):
    with client as request:
        response = post_register(request, HP="bad")

    assert response.status_code == int(HTTPStatus.BAD_REQUEST)

    content = response.content.decode()
    expected = "The home page is invalid, please specify the full HTTP(s) URL."
    assert expected in content


def test_post_register_error_invalid_pgp_fingerprints(client: TestClient):
    with client as request:
        response = post_register(request, K="bad")

    assert response.status_code == int(HTTPStatus.BAD_REQUEST)

    content = response.content.decode()
    expected = "The PGP key fingerprint is invalid."
    assert expected in content

    pk = 'z' + ('a' * 39)
    with client as request:
        response = post_register(request, K=pk)

    assert response.status_code == int(HTTPStatus.BAD_REQUEST)

    content = response.content.decode()
    expected = "The PGP key fingerprint is invalid."
    assert expected in content


def test_post_register_error_invalid_ssh_pubkeys(client: TestClient):
    with client as request:
        response = post_register(request, PK="bad")

    assert response.status_code == int(HTTPStatus.BAD_REQUEST)

    content = response.content.decode()
    assert "The SSH public key is invalid." in content

    with client as request:
        response = post_register(request, PK="ssh-rsa ")

    assert response.status_code == int(HTTPStatus.BAD_REQUEST)

    content = response.content.decode()
    assert "The SSH public key is invalid." in content


def test_post_register_error_unsupported_language(client: TestClient):
    with client as request:
        response = post_register(request, L="bad")

    assert response.status_code == int(HTTPStatus.BAD_REQUEST)

    content = response.content.decode()
    expected = "Language is not currently supported."
    assert expected in content


def test_post_register_error_unsupported_timezone(client: TestClient):
    with client as request:
        response = post_register(request, TZ="ABCDEFGH")

    assert response.status_code == int(HTTPStatus.BAD_REQUEST)

    content = response.content.decode()
    expected = "Timezone is not currently supported."
    assert expected in content


def test_post_register_error_username_taken(client: TestClient, user: User):
    with client as request:
        response = post_register(request, U="test")

    assert response.status_code == int(HTTPStatus.BAD_REQUEST)

    content = response.content.decode()
    expected = r"The username, .*, is already in use."
    assert re.search(expected, content)


def test_post_register_error_email_taken(client: TestClient, user: User):
    with client as request:
        response = post_register(request, E="test@example.org")

    assert response.status_code == int(HTTPStatus.BAD_REQUEST)

    content = response.content.decode()
    expected = r"The address, .*, is already in use."
    assert re.search(expected, content)


def test_post_register_error_ssh_pubkey_taken(client: TestClient, user: User):
    pk = str()

    # Create a public key with ssh-keygen (this adds ssh-keygen as a
    # dependency to passing this test).
    with tempfile.TemporaryDirectory() as tmpdir:
        with open("/dev/null", "w") as null:
            proc = Popen(["ssh-keygen", "-f", f"{tmpdir}/test.ssh", "-N", ""],
                         stdout=null, stderr=null)
            proc.wait()
        assert proc.returncode == 0

        # Read in the public key, then delete the temp dir we made.
        pk = open(f"{tmpdir}/test.ssh.pub").read().rstrip()

    prefix, key, loc = pk.split()
    norm_pk = prefix + " " + key

    # Take the sha256 fingerprint of the ssh public key, create it.
    fp = get_fingerprint(norm_pk)
    with db.begin():
        create(SSHPubKey, UserID=user.ID, PubKey=norm_pk, Fingerprint=fp)

    with client as request:
        response = post_register(request, PK=pk)

    assert response.status_code == int(HTTPStatus.BAD_REQUEST)

    content = response.content.decode()
    expected = r"The SSH public key, .*, is already in use."
    assert re.search(expected, content)


def test_post_register_with_ssh_pubkey(client: TestClient):
    pk = str()

    # Create a public key with ssh-keygen (this adds ssh-keygen as a
    # dependency to passing this test).
    with tempfile.TemporaryDirectory() as tmpdir:
        with open("/dev/null", "w") as null:
            proc = Popen(["ssh-keygen", "-f", f"{tmpdir}/test.ssh", "-N", ""],
                         stdout=null, stderr=null)
            proc.wait()
        assert proc.returncode == 0

        # Read in the public key, then delete the temp dir we made.
        pk = open(f"{tmpdir}/test.ssh.pub").read().rstrip()

    with client as request:
        response = post_register(request, PK=pk)

    assert response.status_code == int(HTTPStatus.OK)


def test_get_account_edit_tu_as_tu(client: TestClient, tu_user: User):
    """ Test edit get route of another TU as a TU. """
    with db.begin():
        user2 = create_user("test2")
        user2.AccountTypeID = at.TRUSTED_USER_ID

    cookies = {"AURSID": tu_user.login(Request(), "testPassword")}
    endpoint = f"/account/{user2.Username}/edit"

    with client as request:
        response = request.get(endpoint, cookies=cookies)
    assert response.status_code == int(HTTPStatus.OK)

    # Verify that we have an account type selection and that the
    # "{at.TRUSTED_USER}" option is selected.
    root = parse_root(response.text)
    atype = root.xpath('//select[@id="id_type"]/option[@selected="selected"]')
    expected = at.TRUSTED_USER
    assert atype[0].text.strip() == expected

    username = root.xpath('//input[@id="id_username"]')[0]
    assert username.attrib["value"] == user2.Username
    email = root.xpath('//input[@id="id_email"]')[0]
    assert email.attrib["value"] == user2.Email


def test_get_account_edit_as_tu(client: TestClient, tu_user: User):
    """ Test edit get route of another user as a TU. """
    with db.begin():
        user2 = create_user("test2")

    cookies = {"AURSID": tu_user.login(Request(), "testPassword")}
    endpoint = f"/account/{user2.Username}/edit"

    with client as request:
        response = request.get(endpoint, cookies=cookies)
    assert response.status_code == int(HTTPStatus.OK)

    # Verify that we have an account type selection and that the
    # "Normal {at.USER}" option is selected.
    root = parse_root(response.text)
    atype = root.xpath('//select[@id="id_type"]/option[@selected="selected"]')
    expected = f"Normal {at.USER}"
    assert atype[0].text.strip() == expected

    # Other fields should be available and match up.
    username = root.xpath('//input[@id="id_username"]')[0]
    assert username.attrib["value"] == user2.Username
    email = root.xpath('//input[@id="id_email"]')[0]
    assert email.attrib["value"] == user2.Email


def test_get_account_edit_type(client: TestClient, user: User):
    """ Test that users do not have an Account Type field. """
    cookies = {"AURSID": user.login(Request(), "testPassword")}
    endpoint = f"/account/{user.Username}/edit"

    with client as request:
        response = request.get(endpoint, cookies=cookies)
    assert response.status_code == int(HTTPStatus.OK)
    assert "id_type" not in response.text


def test_get_account_edit_type_as_tu(client: TestClient, tu_user: User):
    with db.begin():
        user2 = create_user("test_tu")

    cookies = {"AURSID": tu_user.login(Request(), "testPassword")}
    endpoint = f"/account/{user2.Username}/edit"

    with client as request:
        response = request.get(endpoint, cookies=cookies)
    assert response.status_code == int(HTTPStatus.OK)

    root = parse_root(response.text)
    atype = root.xpath('//select[@id="id_type"]/option[@selected="selected"]')
    assert atype[0].text.strip() == f"Normal {at.USER}"


def test_get_account_edit_unauthorized(client: TestClient, user: User):
    request = Request()
    sid = user.login(request, "testPassword")

    with db.begin():
        user2 = create(User, Username="test2", Email="test2@example.org",
                       Passwd="testPassword", AccountTypeID=USER_ID)

    endpoint = f"/account/{user2.Username}/edit"
    with client as request:
        # Try to edit `test2` while authenticated as `test`.
        response = request.get(endpoint, cookies={"AURSID": sid},
                               allow_redirects=False)
    assert response.status_code == int(HTTPStatus.SEE_OTHER)

    expected = f"/account/{user2.Username}"
    assert response.headers.get("location") == expected


def test_post_account_edit(client: TestClient, user: User):
    request = Request()
    sid = user.login(request, "testPassword")

    post_data = {
        "U": "test",
        "E": "test666@example.org",
        "passwd": "testPassword"
    }

    with client as request:
        response = request.post("/account/test/edit", cookies={
            "AURSID": sid
        }, data=post_data, allow_redirects=False)

    assert response.status_code == int(HTTPStatus.OK)

    expected = "The account, <strong>test</strong>, "
    expected += "has been successfully modified."
    assert expected in response.content.decode()


def test_post_account_edit_type_as_tu(client: TestClient, tu_user: User):
    with db.begin():
        user2 = create_user("test_tu")

    cookies = {"AURSID": tu_user.login(Request(), "testPassword")}
    endpoint = f"/account/{user2.Username}/edit"
    data = {
        "U": user2.Username,
        "E": user2.Email,
        "T": at.USER_ID,
        "passwd": "testPassword",
    }
    with client as request:
        resp = request.post(endpoint, data=data, cookies=cookies)
    assert resp.status_code == int(HTTPStatus.OK)


def test_post_account_edit_type_as_dev(client: TestClient, tu_user: User):
    with db.begin():
        user2 = create_user("test2")
        tu_user.AccountTypeID = at.DEVELOPER_ID

    cookies = {"AURSID": tu_user.login(Request(), "testPassword")}
    endpoint = f"/account/{user2.Username}/edit"
    data = {
        "U": user2.Username,
        "E": user2.Email,
        "T": at.DEVELOPER_ID,
        "passwd": "testPassword",
    }
    with client as request:
        resp = request.post(endpoint, data=data, cookies=cookies)
    assert resp.status_code == int(HTTPStatus.OK)
    assert user2.AccountTypeID == at.DEVELOPER_ID


def test_post_account_edit_invalid_type_as_tu(client: TestClient,
                                              tu_user: User):
    with db.begin():
        user2 = create_user("test_tu")
        tu_user.AccountTypeID = at.TRUSTED_USER_ID

    cookies = {"AURSID": tu_user.login(Request(), "testPassword")}
    endpoint = f"/account/{user2.Username}/edit"
    data = {
        "U": user2.Username,
        "E": user2.Email,
        "T": at.DEVELOPER_ID,
        "passwd": "testPassword",
    }
    with client as request:
        resp = request.post(endpoint, data=data, cookies=cookies)
    assert resp.status_code == int(HTTPStatus.BAD_REQUEST)
    assert user2.AccountTypeID == at.USER_ID

    errors = get_errors(resp.text)
    expected = ("You do not have permission to change this user's "
                f"account type to {at.DEVELOPER}.")
    assert errors[0].text.strip() == expected


def test_post_account_edit_dev(client: TestClient, tu_user: User):
    # Modify our user to be a "Trusted User & Developer"
    name = "Trusted User & Developer"
    tu_or_dev = query(AccountType, AccountType.AccountType == name).first()
    with db.begin():
        user.AccountType = tu_or_dev

    request = Request()
    sid = tu_user.login(request, "testPassword")

    post_data = {
        "U": "test",
        "E": "test666@example.org",
        "passwd": "testPassword"
    }

    endpoint = f"/account/{tu_user.Username}/edit"
    with client as request:
        response = request.post(endpoint, cookies={"AURSID": sid},
                                data=post_data, allow_redirects=False)
    assert response.status_code == int(HTTPStatus.OK)

    expected = "The account, <strong>test</strong>, "
    expected += "has been successfully modified."
    assert expected in response.content.decode()


def test_post_account_edit_language(client: TestClient, user: User):
    request = Request()
    sid = user.login(request, "testPassword")

    post_data = {
        "U": "test",
        "E": "test@example.org",
        "L": "de",  # German
        "passwd": "testPassword"
    }

    with client as request:
        response = request.post("/account/test/edit", cookies={
            "AURSID": sid
        }, data=post_data, allow_redirects=False)

    assert response.status_code == int(HTTPStatus.OK)

    # Parse the response content html into an lxml root, then make
    # sure we see a 'de' option selected on the page.
    content = response.content.decode()
    root = lxml.html.fromstring(content)
    lang_nodes = root.xpath('//option[@value="de"]/@selected')
    assert lang_nodes and len(lang_nodes) != 0
    assert lang_nodes[0] == "selected"


def test_post_account_edit_timezone(client: TestClient, user: User):
    request = Request()
    sid = user.login(request, "testPassword")

    post_data = {
        "U": "test",
        "E": "test@example.org",
        "TZ": "CET",
        "passwd": "testPassword"
    }

    with client as request:
        response = request.post("/account/test/edit", cookies={
            "AURSID": sid
        }, data=post_data, allow_redirects=False)

    assert response.status_code == int(HTTPStatus.OK)


def test_post_account_edit_error_missing_password(client: TestClient,
                                                  user: User):
    request = Request()
    sid = user.login(request, "testPassword")

    post_data = {
        "U": "test",
        "E": "test@example.org",
        "TZ": "CET",
        "passwd": ""
    }

    with client as request:
        response = request.post("/account/test/edit", cookies={
            "AURSID": sid
        }, data=post_data, allow_redirects=False)

    assert response.status_code == int(HTTPStatus.BAD_REQUEST)

    content = response.content.decode()
    assert "Invalid password." in content


def test_post_account_edit_error_invalid_password(client: TestClient,
                                                  user: User):
    request = Request()
    sid = user.login(request, "testPassword")

    post_data = {
        "U": "test",
        "E": "test@example.org",
        "TZ": "CET",
        "passwd": "invalid"
    }

    with client as request:
        response = request.post("/account/test/edit", cookies={
            "AURSID": sid
        }, data=post_data, allow_redirects=False)

    assert response.status_code == int(HTTPStatus.BAD_REQUEST)

    content = response.content.decode()
    assert "Invalid password." in content


def test_post_account_edit_suspend_unauthorized(client: TestClient,
                                                user: User):
    cookies = {"AURSID": user.login(Request(), "testPassword")}
    post_data = {
        "U": "test",
        "E": "test@example.org",
        "S": True,
        "passwd": "testPassword"
    }
    with client as request:
        resp = request.post(f"/account/{user.Username}/edit", data=post_data,
                            cookies=cookies)
    assert resp.status_code == int(HTTPStatus.BAD_REQUEST)

    errors = get_errors(resp.text)
    expected = "You do not have permission to suspend accounts."
    assert errors[0].text.strip() == expected


def test_post_account_edit_inactivity(client: TestClient, user: User):
    with db.begin():
        user.AccountTypeID = TRUSTED_USER_ID
    assert not user.Suspended

    cookies = {"AURSID": user.login(Request(), "testPassword")}
    post_data = {
        "U": "test",
        "E": "test@example.org",
        "J": True,
        "passwd": "testPassword"
    }
    with client as request:
        resp = request.post(f"/account/{user.Username}/edit", data=post_data,
                            cookies=cookies)
    assert resp.status_code == int(HTTPStatus.OK)

    # Make sure the user record got updated correctly.
    assert user.InactivityTS > 0

    post_data.update({"J": False})
    with client as request:
        resp = request.post(f"/account/{user.Username}/edit", data=post_data,
                            cookies=cookies)
    assert resp.status_code == int(HTTPStatus.OK)

    assert user.InactivityTS == 0


def test_post_account_edit_suspended(client: TestClient, user: User):
    with db.begin():
        user.AccountTypeID = TRUSTED_USER_ID
    assert not user.Suspended

    cookies = {"AURSID": user.login(Request(), "testPassword")}
    post_data = {
        "U": "test",
        "E": "test@example.org",
        "S": True,
        "passwd": "testPassword"
    }
    endpoint = f"/account/{user.Username}/edit"
    with client as request:
        resp = request.post(endpoint, data=post_data, cookies=cookies)
    assert resp.status_code == int(HTTPStatus.OK)

    # Make sure the user record got updated correctly.
    assert user.Suspended

    post_data.update({"S": False})
    with client as request:
        resp = request.post(endpoint, data=post_data, cookies=cookies)
    assert resp.status_code == int(HTTPStatus.OK)

    assert not user.Suspended


def test_post_account_edit_error_unauthorized(client: TestClient, user: User):
    request = Request()
    sid = user.login(request, "testPassword")

    with db.begin():
        user2 = create(User, Username="test2", Email="test2@example.org",
                       Passwd="testPassword", AccountTypeID=USER_ID)

    post_data = {
        "U": "test",
        "E": "test@example.org",
        "TZ": "CET",
        "passwd": "testPassword"
    }

    endpoint = f"/account/{user2.Username}/edit"
    with client as request:
        # Attempt to edit 'test2' while logged in as 'test'.
        response = request.post(endpoint, cookies={"AURSID": sid},
                                data=post_data, allow_redirects=False)
    assert response.status_code == int(HTTPStatus.SEE_OTHER)

    expected = f"/account/{user2.Username}"
    assert response.headers.get("location") == expected


def test_post_account_edit_ssh_pub_key(client: TestClient, user: User):
    request = Request()
    sid = user.login(request, "testPassword")

    post_data = {
        "U": "test",
        "E": "test@example.org",
        "PK": make_ssh_pubkey(),
        "passwd": "testPassword"
    }

    with client as request:
        response = request.post("/account/test/edit", cookies={
            "AURSID": sid
        }, data=post_data, allow_redirects=False)

    assert response.status_code == int(HTTPStatus.OK)

    # Now let's update what's already there to gain coverage over that path.
    post_data["PK"] = make_ssh_pubkey()

    with client as request:
        response = request.post("/account/test/edit", cookies={
            "AURSID": sid
        }, data=post_data, allow_redirects=False)

    assert response.status_code == int(HTTPStatus.OK)


def test_post_account_edit_missing_ssh_pubkey(client: TestClient, user: User):
    request = Request()
    sid = user.login(request, "testPassword")

    post_data = {
        "U": user.Username,
        "E": user.Email,
        "PK": make_ssh_pubkey(),
        "passwd": "testPassword"
    }

    with client as request:
        response = request.post("/account/test/edit", cookies={
            "AURSID": sid
        }, data=post_data, allow_redirects=False)

    assert response.status_code == int(HTTPStatus.OK)

    post_data = {
        "U": user.Username,
        "E": user.Email,
        "PK": str(),  # Pass an empty string now to walk the delete path.
        "passwd": "testPassword"
    }

    with client as request:
        response = request.post("/account/test/edit", cookies={
            "AURSID": sid
        }, data=post_data, allow_redirects=False)

    assert response.status_code == int(HTTPStatus.OK)


def test_post_account_edit_invalid_ssh_pubkey(client: TestClient, user: User):
    pubkey = "ssh-rsa fake key"

    data = {
        "U": "test",
        "E": "test@example.org",
        "PK": pubkey,
        "passwd": "testPassword"
    }
    cookies = {"AURSID": user.login(Request(), "testPassword")}
    with client as request:
        response = request.post("/account/test/edit", data=data,
                                cookies=cookies, allow_redirects=False)

    assert response.status_code == int(HTTPStatus.BAD_REQUEST)


def test_post_account_edit_password(client: TestClient, user: User):
    request = Request()
    sid = user.login(request, "testPassword")

    post_data = {
        "U": "test",
        "E": "test@example.org",
        "P": "newPassword",
        "C": "newPassword",
        "passwd": "testPassword"
    }

    with client as request:
        response = request.post("/account/test/edit", cookies={
            "AURSID": sid
        }, data=post_data, allow_redirects=False)

    assert response.status_code == int(HTTPStatus.OK)

    assert user.valid_password("newPassword")


def test_post_account_edit_self_type_as_user(client: TestClient, user: User):
    cookies = {"AURSID": user.login(Request(), "testPassword")}
    endpoint = f"/account/{user.Username}/edit"

    with client as request:
        resp = request.get(endpoint, cookies=cookies)
    assert resp.status_code == int(HTTPStatus.OK)
    assert "id_type" not in resp.text

    data = {
        "U": user.Username,
        "E": user.Email,
        "T": TRUSTED_USER_ID,
        "passwd": "testPassword"
    }
    with client as request:
        resp = request.post(endpoint, data=data, cookies=cookies)
    assert resp.status_code == int(HTTPStatus.BAD_REQUEST)

    errors = get_errors(resp.text)
    expected = "You do not have permission to change account types."
    assert errors[0].text.strip() == expected


def test_post_account_edit_other_user_as_user(client: TestClient, user: User):
    with db.begin():
        user2 = create_user("test2")

    cookies = {"AURSID": user.login(Request(), "testPassword")}
    endpoint = f"/account/{user2.Username}/edit"

    with client as request:
        resp = request.get(endpoint, cookies=cookies,
                           allow_redirects=False)
    assert resp.status_code == int(HTTPStatus.SEE_OTHER)
    assert resp.headers.get("location") == f"/account/{user2.Username}"


def test_post_account_edit_self_type_as_tu(client: TestClient, tu_user: User):
    cookies = {"AURSID": tu_user.login(Request(), "testPassword")}
    endpoint = f"/account/{tu_user.Username}/edit"

    # We cannot see the Account Type field on our own edit page.
    with client as request:
        resp = request.get(endpoint, cookies=cookies, allow_redirects=False)
    assert resp.status_code == int(HTTPStatus.OK)
    assert "id_type" in resp.text

    # We cannot modify our own account type.
    data = {
        "U": tu_user.Username,
        "E": tu_user.Email,
        "T": USER_ID,
        "passwd": "testPassword"
    }
    with client as request:
        resp = request.post(endpoint, data=data, cookies=cookies)
    assert resp.status_code == int(HTTPStatus.OK)

    assert tu_user.AccountTypeID == USER_ID


def test_post_account_edit_other_user_type_as_tu(
        client: TestClient, tu_user: User, caplog: pytest.LogCaptureFixture):
    caplog.set_level(DEBUG)

    with db.begin():
        user2 = create_user("test2")

    cookies = {"AURSID": tu_user.login(Request(), "testPassword")}
    endpoint = f"/account/{user2.Username}/edit"

    # As a TU, we can see the Account Type field for other users.
    with client as request:
        resp = request.get(endpoint, cookies=cookies, allow_redirects=False)
    assert resp.status_code == int(HTTPStatus.OK)
    assert "id_type" in resp.text

    # As a TU, we can modify other user's account types.
    data = {
        "U": user2.Username,
        "E": user2.Email,
        "T": TRUSTED_USER_ID,
        "passwd": "testPassword"
    }
    with client as request:
        resp = request.post(endpoint, data=data, cookies=cookies)
    assert resp.status_code == int(HTTPStatus.OK)

    # Let's make sure the DB got updated properly.
    assert user2.AccountTypeID == TRUSTED_USER_ID

    # and also that this got logged out at DEBUG level.
    expected = (f"Trusted User '{tu_user.Username}' has "
                f"modified '{user2.Username}' account's type to"
                f" {TRUSTED_USER}.")
    assert expected in caplog.text


def test_post_account_edit_other_user_type_as_tu_invalid_type(
        client: TestClient, tu_user: User, caplog: pytest.LogCaptureFixture):
    with db.begin():
        user2 = create_user("test2")

    cookies = {"AURSID": tu_user.login(Request(), "testPassword")}
    endpoint = f"/account/{user2.Username}/edit"

    # As a TU, we can modify other user's account types.
    data = {
        "U": user2.Username,
        "E": user2.Email,
        "T": 0,
        "passwd": "testPassword"
    }
    with client as request:
        resp = request.post(endpoint, data=data, cookies=cookies)
    assert resp.status_code == int(HTTPStatus.BAD_REQUEST)

    errors = get_errors(resp.text)
    expected = "Invalid account type provided."
    assert errors[0].text.strip() == expected


def test_get_account(client: TestClient, user: User):
    request = Request()
    sid = user.login(request, "testPassword")

    with client as request:
        response = request.get("/account/test", cookies={"AURSID": sid},
                               allow_redirects=False)

    assert response.status_code == int(HTTPStatus.OK)


def test_get_account_not_found(client: TestClient, user: User):
    request = Request()
    sid = user.login(request, "testPassword")

    with client as request:
        response = request.get("/account/not_found", cookies={"AURSID": sid},
                               allow_redirects=False)

    assert response.status_code == int(HTTPStatus.NOT_FOUND)


def test_get_account_unauthenticated(client: TestClient, user: User):
    with client as request:
        response = request.get("/account/test", allow_redirects=False)
    assert response.status_code == int(HTTPStatus.UNAUTHORIZED)

    content = response.content.decode()
    assert "You must log in to view user information." in content


def test_get_accounts(client: TestClient, user: User, tu_user: User):
    """ Test that we can GET request /accounts and receive
    a form which can be used to POST /accounts. """
    sid = user.login(Request(), "testPassword")
    cookies = {"AURSID": sid}

    with client as request:
        response = request.get("/accounts", cookies=cookies)
    assert response.status_code == int(HTTPStatus.OK)

    parser = lxml.etree.HTMLParser()
    root = lxml.etree.fromstring(response.text, parser=parser)

    # Get the form.
    form = root.xpath('//form[contains(@class, "account-search-form")]')

    # Make sure there's only one form and it goes where it should.
    assert len(form) == 1
    form = next(iter(form))
    assert form.attrib.get("method") == "post"
    assert form.attrib.get("action") == "/accounts"

    def field(element):
        """ Return the given element string as a valid
        selector in the form. """
        return f"./fieldset/p/{element}"

    username = form.xpath(field('input[@id="id_username"]'))
    assert bool(username)

    account_type = form.xpath(field('select[@id="id_type"]'))
    assert bool(account_type)

    suspended = form.xpath(field('input[@id="id_suspended"]'))
    assert bool(suspended)

    email = form.xpath(field('input[@id="id_email"]'))
    assert bool(email)

    realname = form.xpath(field('input[@id="id_realname"]'))
    assert bool(realname)

    irc = form.xpath(field('input[@id="id_irc"]'))
    assert bool(irc)

    sortby = form.xpath(field('select[@id="id_sortby"]'))
    assert bool(sortby)


def parse_root(html):
    parser = lxml.etree.HTMLParser()
    return lxml.etree.fromstring(html, parser=parser)


def get_rows(html):
    root = parse_root(html)
    return root.xpath('//table[contains(@class, "users")]/tbody/tr')


def test_post_accounts(client: TestClient, user: User, tu_user: User):
    # Set a PGPKey.
    with db.begin():
        user.PGPKey = "5F18B20346188419750745D7335F2CB41F253D30"

    # Create a few more users.
    users = [user]
    with db.begin():
        for i in range(10):
            _user = create_user(f"test_{i}")
            users.append(_user)

    sid = user.login(Request(), "testPassword")
    cookies = {"AURSID": sid}

    with client as request:
        response = request.post("/accounts", cookies=cookies)
    assert response.status_code == int(HTTPStatus.OK)

    rows = get_rows(response.text)
    assert len(rows) == 11

    # Simulate default ascending ORDER_BY.
    sorted_users = sorted(users, key=lambda u: u.Username)
    for i, _user in enumerate(sorted_users):
        columns = rows[i].xpath("./td")
        assert len(columns) == 7

        username, atype, suspended, real_name, \
            irc_nick, pgp_key, edit = columns

        username = next(iter(username.xpath("./a")))
        assert username.text.strip() == _user.Username

        assert atype.text.strip() == str(_user.AccountType)
        assert suspended.text.strip() == "Active"
        assert real_name.text == (_user.RealName or None)
        assert irc_nick.text == (_user.IRCNick or None)
        assert pgp_key.text == (_user.PGPKey or None)

        edit = edit.xpath("./a")
        if user.can_edit_user(_user):
            edit = next(iter(edit))
            assert edit.text.strip() == "Edit"
        else:
            assert not edit

        logger.debug('Checked user row {"id": %s, "username": "%s"}.'
                     % (_user.ID, _user.Username))


def test_post_accounts_username(client: TestClient, user: User, tu_user: User):
    # Test the U parameter path.
    sid = user.login(Request(), "testPassword")
    cookies = {"AURSID": sid}

    with client as request:
        response = request.post("/accounts", cookies=cookies,
                                data={"U": user.Username})
    assert response.status_code == int(HTTPStatus.OK)

    rows = get_rows(response.text)
    assert len(rows) == 1

    row = next(iter(rows))
    username, type, status, realname, irc, pgp_key, edit = row

    username = next(iter(username.xpath("./a")))
    assert username.text.strip() == user.Username


def test_post_accounts_account_type(client: TestClient, user: User,
                                    tu_user: User):
    # Check the different account type options.
    sid = user.login(Request(), "testPassword")
    cookies = {"AURSID": sid}

    # Make a user with the "User" role here so we can
    # test the `u` parameter.
    account_type = query(AccountType,
                         AccountType.AccountType == "User").first()
    with db.begin():
        create(User, Username="test_2",
               Email="test_2@example.org",
               RealName="Test User 2",
               Passwd="testPassword",
               AccountType=account_type)

    # Expect no entries; we marked our only user as a User type.
    with client as request:
        response = request.post("/accounts", cookies=cookies,
                                data={"T": "t"})
    assert response.status_code == int(HTTPStatus.OK)
    assert len(get_rows(response.text)) == 0

    # So, let's also ensure that specifying "u" returns our user.
    with client as request:
        response = request.post("/accounts", cookies=cookies,
                                data={"T": "u"})
    assert response.status_code == int(HTTPStatus.OK)

    rows = get_rows(response.text)
    assert len(rows) == 1

    row = next(iter(rows))
    username, type, status, realname, irc, pgp_key, edit = row

    assert type.text.strip() == "User"

    # Set our only user to a Trusted User.
    with db.begin():
        user.AccountType = query(AccountType).filter(
            AccountType.ID == TRUSTED_USER_ID
        ).first()

    with client as request:
        response = request.post("/accounts", cookies=cookies,
                                data={"T": "t"})
    assert response.status_code == int(HTTPStatus.OK)

    rows = get_rows(response.text)
    assert len(rows) == 1

    row = next(iter(rows))
    username, type, status, realname, irc, pgp_key, edit = row

    assert type.text.strip() == "Trusted User"

    with db.begin():
        user.AccountType = query(AccountType).filter(
            AccountType.ID == DEVELOPER_ID
        ).first()

    with client as request:
        response = request.post("/accounts", cookies=cookies,
                                data={"T": "d"})
    assert response.status_code == int(HTTPStatus.OK)

    rows = get_rows(response.text)
    assert len(rows) == 1

    row = next(iter(rows))
    username, type, status, realname, irc, pgp_key, edit = row

    assert type.text.strip() == "Developer"

    with db.begin():
        user.AccountType = query(AccountType).filter(
            AccountType.ID == TRUSTED_USER_AND_DEV_ID
        ).first()

    with client as request:
        response = request.post("/accounts", cookies=cookies,
                                data={"T": "td"})
    assert response.status_code == int(HTTPStatus.OK)

    rows = get_rows(response.text)
    assert len(rows) == 1

    row = next(iter(rows))
    username, type, status, realname, irc, pgp_key, edit = row

    assert type.text.strip() == "Trusted User & Developer"


def test_post_accounts_status(client: TestClient, user: User, tu_user: User):
    # Test the functionality of Suspended.
    sid = user.login(Request(), "testPassword")
    cookies = {"AURSID": sid}

    with client as request:
        response = request.post("/accounts", cookies=cookies)
    assert response.status_code == int(HTTPStatus.OK)

    rows = get_rows(response.text)
    assert len(rows) == 1

    row = next(iter(rows))
    username, type, status, realname, irc, pgp_key, edit = row
    assert status.text.strip() == "Active"

    with db.begin():
        user.Suspended = True

    with client as request:
        response = request.post("/accounts", cookies=cookies,
                                data={"S": True})
    assert response.status_code == int(HTTPStatus.OK)

    rows = get_rows(response.text)
    assert len(rows) == 1

    row = next(iter(rows))
    username, type, status, realname, irc, pgp_key, edit = row
    assert status.text.strip() == "Suspended"


def test_post_accounts_email(client: TestClient, user: User, tu_user: User):
    sid = user.login(Request(), "testPassword")
    cookies = {"AURSID": sid}

    # Search via email.
    with client as request:
        response = request.post("/accounts", cookies=cookies,
                                data={"E": user.Email})
    assert response.status_code == int(HTTPStatus.OK)

    rows = get_rows(response.text)
    assert len(rows) == 1


def test_post_accounts_realname(client: TestClient, user: User, tu_user: User):
    # Test the R parameter path.
    sid = user.login(Request(), "testPassword")
    cookies = {"AURSID": sid}

    with client as request:
        response = request.post("/accounts", cookies=cookies,
                                data={"R": user.RealName})
    assert response.status_code == int(HTTPStatus.OK)

    rows = get_rows(response.text)
    assert len(rows) == 1


def test_post_accounts_irc(client: TestClient, user: User, tu_user: User):
    # Test the I parameter path.
    sid = user.login(Request(), "testPassword")
    cookies = {"AURSID": sid}

    with client as request:
        response = request.post("/accounts", cookies=cookies,
                                data={"I": user.IRCNick})
    assert response.status_code == int(HTTPStatus.OK)

    rows = get_rows(response.text)
    assert len(rows) == 1


def test_post_accounts_sortby(client: TestClient, user: User, tu_user: User):
    # Create a second user so we can compare sorts.
    with db.begin():
        user_ = create_user("test2")
        user_.AccountTypeID = DEVELOPER_ID

    sid = user.login(Request(), "testPassword")
    cookies = {"AURSID": sid}

    # Show that "u" is the default search order, by username.
    with client as request:
        response = request.post("/accounts", cookies=cookies)
    assert response.status_code == int(HTTPStatus.OK)
    rows = get_rows(response.text)
    assert len(rows) == 2
    first_rows = rows

    with client as request:
        response = request.post("/accounts", cookies=cookies,
                                data={"SB": "u"})
    assert response.status_code == int(HTTPStatus.OK)
    rows = get_rows(response.text)
    assert len(rows) == 2

    def compare_text_values(column, lhs, rhs):
        return [row[column].text for row in lhs] \
            == [row[column].text for row in rhs]

    # Test the username rows are ordered the same.
    assert compare_text_values(0, first_rows, rows) is True

    with client as request:
        response = request.post("/accounts", cookies=cookies,
                                data={"SB": "i"})
    assert response.status_code == int(HTTPStatus.OK)
    rows = get_rows(response.text)
    assert len(rows) == 2

    # Test the rows are reversed when ordering by IRCNick.
    assert compare_text_values(4, first_rows, reversed(rows)) is True

    # Sort by "i" -> RealName.
    with client as request:
        response = request.post("/accounts", cookies=cookies,
                                data={"SB": "r"})
    assert response.status_code == int(HTTPStatus.OK)
    rows = get_rows(response.text)
    assert len(rows) == 2

    # Test the rows are reversed when ordering by RealName.
    assert compare_text_values(4, first_rows, reversed(rows)) is True

    with db.begin():
        user.AccountType = query(AccountType).filter(
            AccountType.ID == TRUSTED_USER_AND_DEV_ID
        ).first()

    # Fetch first_rows again with our new AccountType ordering.
    with client as request:
        response = request.post("/accounts", cookies=cookies)
    assert response.status_code == int(HTTPStatus.OK)
    rows = get_rows(response.text)
    assert len(rows) == 2
    first_rows = rows

    # Sort by "t" -> AccountType.
    with client as request:
        response = request.post("/accounts", cookies=cookies,
                                data={"SB": "t"})
    assert response.status_code == int(HTTPStatus.OK)
    rows = get_rows(response.text)
    assert len(rows) == 2

    # Test that rows again got reversed.
    assert compare_text_values(1, first_rows, reversed(rows))


def test_post_accounts_pgp_key(client: TestClient, user: User, tu_user: User):
    with db.begin():
        user.PGPKey = "5F18B20346188419750745D7335F2CB41F253D30"

    sid = user.login(Request(), "testPassword")
    cookies = {"AURSID": sid}

    # Search via PGPKey.
    with client as request:
        response = request.post("/accounts", cookies=cookies,
                                data={"K": user.PGPKey})
    assert response.status_code == int(HTTPStatus.OK)

    rows = get_rows(response.text)
    assert len(rows) == 1


def test_post_accounts_paged(client: TestClient, user: User, tu_user: User):
    # Create 150 users.
    users = [user]
    account_type = query(AccountType,
                         AccountType.AccountType == "User").first()
    with db.begin():
        for i in range(150):
            _user = create(User, Username=f"test_#{i}",
                           Email=f"test_#{i}@example.org",
                           RealName=f"Test User #{i}",
                           Passwd="testPassword",
                           AccountType=account_type)
            users.append(_user)

    sid = user.login(Request(), "testPassword")
    cookies = {"AURSID": sid}

    with client as request:
        response = request.post("/accounts", cookies=cookies)
    assert response.status_code == int(HTTPStatus.OK)

    rows = get_rows(response.text)
    assert len(rows) == 50  # `pp`, or hits per page is defined at 50.

    # Sort users in ascending default sort by order.
    sorted_users = sorted(users, key=lambda u: u.Username)

    # Get the first fifty sorted users and assert that's what
    # we got in the first search result page.
    first_fifty = sorted_users[:50]

    for i, _user in enumerate(first_fifty):
        row = rows[i]
        username = row[0].xpath("./a")[0]  # First column
        assert username.text.strip() == _user.Username

    root = parse_root(response.text)
    page_prev = root.xpath('//button[contains(@class, "page-prev")]')[0]
    page_next = root.xpath('//button[contains(@class, "page-next")]')[0]

    assert page_prev.attrib["disabled"] == "disabled"
    assert "disabled" not in page_next.attrib

    with client as request:
        response = request.post("/accounts", cookies=cookies,
                                data={"O": 50})  # +50 offset.
    assert response.status_code == int(HTTPStatus.OK)

    rows = get_rows(response.text)
    assert len(rows) == 50

    second_fifty = sorted_users[50:100]

    for i, _user in enumerate(second_fifty):
        row = rows[i]
        username = row[0].xpath("./a")[0]  # First column
        assert username.text.strip() == _user.Username

    with client as request:
        response = request.post("/accounts", cookies=cookies,
                                data={"O": 101})  # Last page.
    assert response.status_code == int(HTTPStatus.OK)

    rows = get_rows(response.text)
    assert len(rows) == 50

    root = parse_root(response.text)
    page_prev = root.xpath('//button[contains(@class, "page-prev")]')[0]
    page_next = root.xpath('//button[contains(@class, "page-next")]')[0]

    assert "disabled" not in page_prev.attrib
    assert page_next.attrib["disabled"] == "disabled"


def test_get_terms_of_service(client: TestClient, user: User):
    with db.begin():
        term = create(Term, Description="Test term.",
                      URL="http://localhost", Revision=1)

    with client as request:
        response = request.get("/tos", allow_redirects=False)
    assert response.status_code == int(HTTPStatus.SEE_OTHER)

    request = Request()
    sid = user.login(request, "testPassword")
    cookies = {"AURSID": sid}

    # First of all, let's test that we get redirected to /tos
    # when attempting to browse authenticated without accepting terms.
    with client as request:
        response = request.get("/", cookies=cookies, allow_redirects=False)
    assert response.status_code == int(HTTPStatus.SEE_OTHER)
    assert response.headers.get("location") == "/tos"

    with client as request:
        response = request.get("/tos", cookies=cookies, allow_redirects=False)
    assert response.status_code == int(HTTPStatus.OK)

    with db.begin():
        accepted_term = create(AcceptedTerm, User=user,
                               Term=term, Revision=term.Revision)

    with client as request:
        response = request.get("/tos", cookies=cookies, allow_redirects=False)
    # We accepted the term, there's nothing left to accept.
    assert response.status_code == int(HTTPStatus.SEE_OTHER)

    # Bump the term's revision.
    with db.begin():
        term.Revision = 2

    with client as request:
        response = request.get("/tos", cookies=cookies, allow_redirects=False)
    # This time, we have a modified term Revision that hasn't
    # yet been agreed to via AcceptedTerm update.
    assert response.status_code == int(HTTPStatus.OK)

    with db.begin():
        accepted_term.Revision = term.Revision

    with client as request:
        response = request.get("/tos", cookies=cookies, allow_redirects=False)
    # We updated the term revision, there's nothing left to accept.
    assert response.status_code == int(HTTPStatus.SEE_OTHER)


def test_post_terms_of_service(client: TestClient, user: User):
    request = Request()
    sid = user.login(request, "testPassword")

    data = {"accept": True}  # POST data.
    cookies = {"AURSID": sid}  # Auth cookie.

    # Create a fresh Term.
    with db.begin():
        term = create(Term, Description="Test term.",
                      URL="http://localhost", Revision=1)

    # Test that the term we just created is listed.
    with client as request:
        response = request.get("/tos", cookies=cookies)
    assert response.status_code == int(HTTPStatus.OK)

    # Make a POST request to /tos with the agree checkbox disabled (False).
    with client as request:
        response = request.post("/tos", data={"accept": False},
                                cookies=cookies)
    assert response.status_code == int(HTTPStatus.OK)

    # Make a POST request to /tos with the agree checkbox enabled (True).
    with client as request:
        response = request.post("/tos", data=data, cookies=cookies)
    assert response.status_code == int(HTTPStatus.SEE_OTHER)

    # Query the db for the record created by the post request.
    accepted_term = query(AcceptedTerm,
                          AcceptedTerm.TermsID == term.ID).first()
    assert accepted_term.User == user
    assert accepted_term.Term == term

    # Update the term to revision 2.
    with db.begin():
        term.Revision = 2

    # A GET request gives us the new revision to accept.
    with client as request:
        response = request.get("/tos", cookies=cookies)
    assert response.status_code == int(HTTPStatus.OK)

    # Let's POST again and agree to the new term revision.
    with client as request:
        response = request.post("/tos", data=data, cookies=cookies)
    assert response.status_code == int(HTTPStatus.SEE_OTHER)

    # Check that the records ended up matching.
    assert accepted_term.Revision == term.Revision

    # Now, see that GET redirects us to / with no terms left to accept.
    with client as request:
        response = request.get("/tos", cookies=cookies, allow_redirects=False)
    assert response.status_code == int(HTTPStatus.SEE_OTHER)
    assert response.headers.get("location") == "/"


def test_account_comments_not_found(client: TestClient, user: User):
    cookies = {"AURSID": user.login(Request(), "testPassword")}
    with client as request:
        resp = request.get("/account/non-existent/comments", cookies=cookies)
    assert resp.status_code == int(HTTPStatus.NOT_FOUND)


def test_accounts_unauthorized(client: TestClient, user: User):
    cookies = {"AURSID": user.login(Request(), "testPassword")}
    with client as request:
        resp = request.get("/accounts", cookies=cookies, allow_redirects=False)
    assert resp.status_code == int(HTTPStatus.SEE_OTHER)
    assert resp.headers.get("location") == "/"
