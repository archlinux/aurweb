import os
import tempfile

from subprocess import PIPE, Popen

from sqlalchemy.orm import backref, relationship

from aurweb import schema
from aurweb.models.declarative import Base


class SSHPubKey(Base):
    __table__ = schema.SSHPubKeys
    __tablename__ = __table__.name
    __mapper_args__ = {"primary_key": [__table__.c.Fingerprint]}

    User = relationship(
        "User", backref=backref("ssh_pub_key", uselist=False),
        foreign_keys=[__table__.c.UserID])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


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
