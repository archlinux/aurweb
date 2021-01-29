import re
import tempfile

from datetime import datetime
from http import HTTPStatus
from subprocess import Popen

import lxml.html
import pytest

from fastapi.testclient import TestClient

from aurweb import captcha
from aurweb.asgi import app
from aurweb.db import create, delete, query
from aurweb.models.account_type import AccountType
from aurweb.models.ban import Ban
from aurweb.models.session import Session
from aurweb.models.ssh_pub_key import SSHPubKey, get_fingerprint
from aurweb.models.user import User
from aurweb.testing import setup_test_db
from aurweb.testing.models import make_user
from aurweb.testing.requests import Request

# Some test global constants.
TEST_USERNAME = "test"
TEST_EMAIL = "test@example.org"

# Global mutables.
client = TestClient(app)
user = None


@pytest.fixture(autouse=True)
def setup():
    global user

    setup_test_db("Users", "Sessions", "Bans")

    account_type = query(AccountType,
                         AccountType.AccountType == "User").first()
    user = make_user(Username=TEST_USERNAME, Email=TEST_EMAIL,
                     RealName="Test User", Passwd="testPassword",
                     AccountType=account_type)


def test_get_passreset_authed_redirects():
    sid = user.login(Request(), "testPassword")
    assert sid is not None

    with client as request:
        response = request.get("/passreset", cookies={"AURSID": sid},
                               allow_redirects=False)

    assert response.status_code == int(HTTPStatus.SEE_OTHER)
    assert response.headers.get("location") == "/"


def test_get_passreset():
    with client as request:
        response = request.get("/passreset")
    assert response.status_code == int(HTTPStatus.OK)


def test_get_passreset_translation():
    # Test that translation works; set it to de.
    with client as request:
        response = request.get("/passreset", cookies={"AURLANG": "de"})

    # The header title should be translated.
    assert "Passwort zurücksetzen".encode("utf-8") in response.content

    # The form input label should be translated.
    assert "Benutzername oder primäre E-Mail-Adresse eingeben:".encode(
        "utf-8") in response.content

    # And the button.
    assert "Weiter".encode("utf-8") in response.content

    # Restore english.
    with client as request:
        response = request.get("/passreset", cookies={"AURLANG": "en"})


def test_get_passreset_with_resetkey():
    with client as request:
        response = request.get("/passreset", data={"resetkey": "abcd"})
    assert response.status_code == int(HTTPStatus.OK)


def test_post_passreset_authed_redirects():
    sid = user.login(Request(), "testPassword")
    assert sid is not None

    with client as request:
        response = request.post("/passreset",
                                cookies={"AURSID": sid},
                                data={"user": "blah"},
                                allow_redirects=False)

    assert response.status_code == int(HTTPStatus.SEE_OTHER)
    assert response.headers.get("location") == "/"


def test_post_passreset_user():
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


def test_post_passreset_resetkey():
    from aurweb.db import session

    user.session = Session(UsersID=user.ID, SessionID="blah",
                           LastUpdateTS=datetime.utcnow().timestamp())
    session.commit()

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


def test_post_passreset_error_invalid_email():
    # First, test with a user that doesn't even exist.
    with client as request:
        response = request.post("/passreset", data={"user": "invalid"})
    assert response.status_code == int(HTTPStatus.NOT_FOUND)

    error = "Invalid e-mail."
    assert error in response.content.decode("utf-8")

    # Then, test with an invalid resetkey for a real user.
    _ = make_resetkey()
    post_data = make_passreset_data("fake")
    post_data["password"] = "abcd1234"
    post_data["confirm"] = "abcd1234"

    with client as request:
        response = request.post("/passreset", data=post_data)
    assert response.status_code == int(HTTPStatus.NOT_FOUND)
    assert error in response.content.decode("utf-8")


def make_resetkey():
    with client as request:
        response = request.post("/passreset", data={"user": TEST_USERNAME})
        assert response.status_code == int(HTTPStatus.SEE_OTHER)
        assert response.headers.get("location") == "/passreset?step=confirm"
    return user.ResetKey


def make_passreset_data(resetkey):
    return {
        "user": user.Username,
        "resetkey": resetkey
    }


def test_post_passreset_error_missing_field():
    # Now that we've prepared the password reset, prepare a POST
    # request with the user's ResetKey.
    resetkey = make_resetkey()
    post_data = make_passreset_data(resetkey)

    with client as request:
        response = request.post("/passreset", data=post_data)

    assert response.status_code == int(HTTPStatus.BAD_REQUEST)

    error = "Missing a required field."
    assert error in response.content.decode("utf-8")


def test_post_passreset_error_password_mismatch():
    resetkey = make_resetkey()
    post_data = make_passreset_data(resetkey)

    post_data["password"] = "abcd1234"
    post_data["confirm"] = "mismatched"

    with client as request:
        response = request.post("/passreset", data=post_data)

    assert response.status_code == int(HTTPStatus.BAD_REQUEST)

    error = "Password fields do not match."
    assert error in response.content.decode("utf-8")


def test_post_passreset_error_password_requirements():
    resetkey = make_resetkey()
    post_data = make_passreset_data(resetkey)

    passwd_min_len = User.minimum_passwd_length()
    assert passwd_min_len >= 4

    post_data["password"] = "x"
    post_data["confirm"] = "x"

    with client as request:
        response = request.post("/passreset", data=post_data)

    assert response.status_code == int(HTTPStatus.BAD_REQUEST)

    error = f"Your password must be at least {passwd_min_len} characters."
    assert error in response.content.decode("utf-8")


def test_get_register():
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


def test_post_register():
    with client as request:
        response = post_register(request)
    assert response.status_code == int(HTTPStatus.OK)

    expected = "The account, <strong>'newUser'</strong>, "
    expected += "has been successfully created."
    assert expected in response.content.decode()


def test_post_register_rejects_case_insensitive_spoof():
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


def test_post_register_error_expired_captcha():
    with client as request:
        response = post_register(request, captcha_salt="invalid-salt")

    assert response.status_code == int(HTTPStatus.BAD_REQUEST)

    content = response.content.decode()
    assert "This CAPTCHA has expired. Please try again." in content


def test_post_register_error_missing_captcha():
    with client as request:
        response = post_register(request, captcha=None)

    assert response.status_code == int(HTTPStatus.BAD_REQUEST)

    content = response.content.decode()
    assert "The CAPTCHA is missing." in content


def test_post_register_error_invalid_captcha():
    with client as request:
        response = post_register(request, captcha="invalid blah blah")

    assert response.status_code == int(HTTPStatus.BAD_REQUEST)

    content = response.content.decode()
    assert "The entered CAPTCHA answer is invalid." in content


def test_post_register_error_ip_banned():
    # 'testclient' is used as request.client.host via FastAPI TestClient.
    create(Ban, IPAddress="testclient", BanTS=datetime.utcnow())

    with client as request:
        response = post_register(request)

    assert response.status_code == int(HTTPStatus.BAD_REQUEST)

    content = response.content.decode()
    assert ("Account registration has been disabled for your IP address, " +
            "probably due to sustained spam attacks. Sorry for the " +
            "inconvenience.") in content


def test_post_register_error_missing_username():
    with client as request:
        response = post_register(request, U="")

    assert response.status_code == int(HTTPStatus.BAD_REQUEST)

    content = response.content.decode()
    assert "Missing a required field." in content


def test_post_register_error_missing_email():
    with client as request:
        response = post_register(request, E="")

    assert response.status_code == int(HTTPStatus.BAD_REQUEST)

    content = response.content.decode()
    assert "Missing a required field." in content


def test_post_register_error_invalid_username():
    with client as request:
        # Our test config requires at least three characters for a
        # valid username, so test against two characters: 'ba'.
        response = post_register(request, U="ba")

    assert response.status_code == int(HTTPStatus.BAD_REQUEST)

    content = response.content.decode()
    assert "The username is invalid." in content


def test_post_register_invalid_password():
    with client as request:
        response = post_register(request, P="abc", C="abc")

    assert response.status_code == int(HTTPStatus.BAD_REQUEST)

    content = response.content.decode()
    expected = r"Your password must be at least \d+ characters."
    assert re.search(expected, content)


def test_post_register_error_missing_confirm():
    with client as request:
        response = post_register(request, C=None)

    assert response.status_code == int(HTTPStatus.BAD_REQUEST)

    content = response.content.decode()
    assert "Please confirm your new password." in content


def test_post_register_error_mismatched_confirm():
    with client as request:
        response = post_register(request, C="mismatched")

    assert response.status_code == int(HTTPStatus.BAD_REQUEST)

    content = response.content.decode()
    assert "Password fields do not match." in content


def test_post_register_error_invalid_email():
    with client as request:
        response = post_register(request, E="bad@email")

    assert response.status_code == int(HTTPStatus.BAD_REQUEST)

    content = response.content.decode()
    assert "The email address is invalid." in content


def test_post_register_error_undeliverable_email():
    with client as request:
        # At the time of writing, webchat.freenode.net does not contain
        # mx records; if it ever does, it'll break this test.
        response = post_register(request, E="email@bad.c")

    assert response.status_code == int(HTTPStatus.BAD_REQUEST)

    content = response.content.decode()
    assert "The email address is invalid." in content


def test_post_register_invalid_backup_email():
    with client as request:
        response = post_register(request, BE="bad@email")

    assert response.status_code == int(HTTPStatus.BAD_REQUEST)

    content = response.content.decode()
    assert "The backup email address is invalid." in content


def test_post_register_error_invalid_homepage():
    with client as request:
        response = post_register(request, HP="bad")

    assert response.status_code == int(HTTPStatus.BAD_REQUEST)

    content = response.content.decode()
    expected = "The home page is invalid, please specify the full HTTP(s) URL."
    assert expected in content


def test_post_register_error_invalid_pgp_fingerprints():
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


def test_post_register_error_invalid_ssh_pubkeys():
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


def test_post_register_error_unsupported_language():
    with client as request:
        response = post_register(request, L="bad")

    assert response.status_code == int(HTTPStatus.BAD_REQUEST)

    content = response.content.decode()
    expected = "Language is not currently supported."
    assert expected in content


def test_post_register_error_unsupported_timezone():
    with client as request:
        response = post_register(request, TZ="ABCDEFGH")

    assert response.status_code == int(HTTPStatus.BAD_REQUEST)

    content = response.content.decode()
    expected = "Timezone is not currently supported."
    assert expected in content


def test_post_register_error_username_taken():
    with client as request:
        response = post_register(request, U="test")

    assert response.status_code == int(HTTPStatus.BAD_REQUEST)

    content = response.content.decode()
    expected = r"The username, .*, is already in use."
    assert re.search(expected, content)


def test_post_register_error_email_taken():
    with client as request:
        response = post_register(request, E="test@example.org")

    assert response.status_code == int(HTTPStatus.BAD_REQUEST)

    content = response.content.decode()
    expected = r"The address, .*, is already in use."
    assert re.search(expected, content)


def test_post_register_error_ssh_pubkey_taken():
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

    # Take the sha256 fingerprint of the ssh public key, create it.
    fp = get_fingerprint(pk)
    create(SSHPubKey, UserID=user.ID, PubKey=pk, Fingerprint=fp)

    with client as request:
        response = post_register(request, PK=pk)

    assert response.status_code == int(HTTPStatus.BAD_REQUEST)

    content = response.content.decode()
    expected = r"The SSH public key, .*, is already in use."
    assert re.search(expected, content)


def test_post_register_with_ssh_pubkey():
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


def test_get_account_edit():
    request = Request()
    sid = user.login(request, "testPassword")

    with client as request:
        response = request.get("/account/test/edit", cookies={
            "AURSID": sid
        }, allow_redirects=False)

    assert response.status_code == int(HTTPStatus.OK)


def test_get_account_edit_unauthorized():
    request = Request()
    sid = user.login(request, "testPassword")

    create(User, Username="test2", Email="test2@example.org",
           Passwd="testPassword")

    with client as request:
        # Try to edit `test2` while authenticated as `test`.
        response = request.get("/account/test2/edit", cookies={
            "AURSID": sid
        }, allow_redirects=False)

    assert response.status_code == int(HTTPStatus.UNAUTHORIZED)


def test_post_account_edit():
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


def test_post_account_edit_dev():
    from aurweb.db import session

    # Modify our user to be a "Trusted User & Developer"
    name = "Trusted User & Developer"
    tu_or_dev = query(AccountType, AccountType.AccountType == name).first()
    user.AccountType = tu_or_dev
    session.commit()

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


def test_post_account_edit_language():
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


def test_post_account_edit_timezone():
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


def test_post_account_edit_error_missing_password():
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


def test_post_account_edit_error_invalid_password():
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


def test_post_account_edit_error_unauthorized():
    request = Request()
    sid = user.login(request, "testPassword")

    test2 = create(User, Username="test2", Email="test2@example.org",
                   Passwd="testPassword")

    post_data = {
        "U": "test",
        "E": "test@example.org",
        "TZ": "CET",
        "passwd": "testPassword"
    }

    with client as request:
        # Attempt to edit 'test2' while logged in as 'test'.
        response = request.post("/account/test2/edit", cookies={
            "AURSID": sid
        }, data=post_data, allow_redirects=False)

    assert response.status_code == int(HTTPStatus.UNAUTHORIZED)


def test_post_account_edit_ssh_pub_key():
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

    request = Request()
    sid = user.login(request, "testPassword")

    post_data = {
        "U": "test",
        "E": "test@example.org",
        "PK": pk,
        "passwd": "testPassword"
    }

    with client as request:
        response = request.post("/account/test/edit", cookies={
            "AURSID": sid
        }, data=post_data, allow_redirects=False)

    assert response.status_code == int(HTTPStatus.OK)

    # Now let's update what's already there to gain coverage over that path.
    pk = str()
    with tempfile.TemporaryDirectory() as tmpdir:
        with open("/dev/null", "w") as null:
            proc = Popen(["ssh-keygen", "-f", f"{tmpdir}/test.ssh", "-N", ""],
                         stdout=null, stderr=null)
            proc.wait()
        assert proc.returncode == 0

        # Read in the public key, then delete the temp dir we made.
        pk = open(f"{tmpdir}/test.ssh.pub").read().rstrip()

    post_data["PK"] = pk

    with client as request:
        response = request.post("/account/test/edit", cookies={
            "AURSID": sid
        }, data=post_data, allow_redirects=False)

    assert response.status_code == int(HTTPStatus.OK)


def test_post_account_edit_invalid_ssh_pubkey():
    pubkey = "ssh-rsa fake key"

    request = Request()
    sid = user.login(request, "testPassword")

    post_data = {
        "U": "test",
        "E": "test@example.org",
        "P": "newPassword",
        "C": "newPassword",
        "PK": pubkey,
        "passwd": "testPassword"
    }

    with client as request:
        response = request.post("/account/test/edit", cookies={
            "AURSID": sid
        }, data=post_data, allow_redirects=False)

    assert response.status_code == int(HTTPStatus.BAD_REQUEST)


def test_post_account_edit_password():
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


>>>>>> > dddd1137... add account edit(settings) routes
