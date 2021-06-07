import os
import tempfile

from subprocess import PIPE, Popen

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import backref, relationship

from aurweb.models.declarative import Base


class SSHPubKey(Base):
    __tablename__ = "SSHPubKeys"

    UserID = Column(
        Integer, ForeignKey("Users.ID", ondelete="CASCADE"),
        nullable=False)
    User = relationship(
        "User", backref=backref("ssh_pub_key", uselist=False),
        foreign_keys=[UserID])

    Fingerprint = Column(String(44), primary_key=True)

    __mapper_args__ = {"primary_key": Fingerprint}

    def __init__(self, **kwargs):
        self.UserID = kwargs.get("UserID")
        self.Fingerprint = kwargs.get("Fingerprint")
        self.PubKey = kwargs.get("PubKey")


def get_fingerprint(pubkey):
    with tempfile.TemporaryDirectory() as tmpdir:
        pk = os.path.join(tmpdir, "ssh.pub")

        with open(pk, "w") as f:
            f.write(pubkey)

        proc = Popen(["ssh-keygen", "-l", "-f", pk], stdout=PIPE, stderr=PIPE)
        out, err = proc.communicate()

        # Invalid SSH Public Key. Return None to the caller.
        if proc.returncode != 0:
            return None

        parts = out.decode().split()
        fp = parts[1].replace("SHA256:", "")

    return fp
