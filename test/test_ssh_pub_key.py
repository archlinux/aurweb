from subprocess import PIPE, Popen
from typing import Generator

import pytest

from aurweb import db
from aurweb.models.account_type import USER_ID
from aurweb.models.ssh_pub_key import SSHPubKey, get_fingerprint
from aurweb.models.user import User

TEST_SSH_PUBKEY = """
ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQCycoCi5yGCvSclH2wmNBUuwsYEzRZZBJaQquRc4y\
sl+Tg+/jiDkR3Zn9fIznC4KnFoyrIHzkKuePZ3bNDYwkZxkJKoWBCh4hXKDXSm87FMN0+VDC+1QxF/\
z0XaAGr/P6f4XukabyddypBdnHcZiplbw+YOSqcAE2TCqOlSXwNMOcF9U89UsR/Q9i9I52hlvU0q8+\
fZVGhou1KCowFSnHYtrr5KYJ04CXkJ13DkVf3+pjQWyrByvBcf1hGEaczlgfobrrv/y96jDhgfXucx\
liNKLdufDPPkii3LhhsNcDmmI1VZ3v0irKvd9WZuauqloobY84zEFcDTyjn0hxGjVeYFejm4fBnvjg\
a0yZXORuWksdNfXWLDxFk6MDDd1jF0ExRbP+OxDuU4IVyIuDL7S3cnbf2YjGhkms/8voYT2OBE7FwN\
lfv98Kr0NUp51zpf55Arxn9j0Rz9xTA7FiODQgCn6iQ0SDtzUNL0IKTCw26xJY5gzMxbfpvzPQGeul\
x/ioM= kevr@volcano
"""


@pytest.fixture(autouse=True)
def setup(db_test):
    return


@pytest.fixture
def user() -> Generator[User]:
    with db.begin():
        user = db.create(
            User,
            Username="test",
            Email="test@example.org",
            RealName="Test User",
            Passwd="testPassword",
            AccountTypeID=USER_ID,
        )
    yield user


@pytest.fixture
def pubkey(user: User) -> Generator[SSHPubKey]:
    with db.begin():
        pubkey = db.create(
            SSHPubKey, User=user, Fingerprint="testFingerprint", PubKey="testPubKey"
        )
    yield pubkey


def test_pubkey(user: User, pubkey: SSHPubKey):
    assert pubkey.UserID == user.ID
    assert pubkey.User == user
    assert pubkey.Fingerprint == "testFingerprint"
    assert pubkey.PubKey == "testPubKey"


def test_pubkey_cs(user: User):
    """Test case sensitivity of the database table."""
    with db.begin():
        pubkey_cs = db.create(
            SSHPubKey, User=user, Fingerprint="TESTFINGERPRINT", PubKey="TESTPUBKEY"
        )

    assert pubkey_cs.Fingerprint == "TESTFINGERPRINT"
    assert pubkey_cs.Fingerprint != "testFingerprint"
    assert pubkey_cs.PubKey == "TESTPUBKEY"
    assert pubkey_cs.PubKey != "testPubKey"


def test_pubkey_fingerprint():
    proc = Popen(["ssh-keygen", "-l", "-f", "-"], stdin=PIPE, stdout=PIPE)
    out, _ = proc.communicate(TEST_SSH_PUBKEY.encode())
    expected = out.decode().split()[1].split(":", 1)[1]
    assert get_fingerprint(TEST_SSH_PUBKEY) == expected


def test_pubkey_invalid_fingerprint():
    with pytest.raises(ValueError):
        get_fingerprint("invalid-prefix some-fake-content")
