from subprocess import PIPE, Popen

from sqlalchemy.orm import backref, relationship

from aurweb import schema
from aurweb.models.declarative import Base


class SSHPubKey(Base):
    __table__ = schema.SSHPubKeys
    __tablename__ = __table__.name
    __mapper_args__ = {"primary_key": [__table__.c.Fingerprint]}

    User = relationship(
        "User", backref=backref("ssh_pub_keys", lazy="dynamic"),
        foreign_keys=[__table__.c.UserID])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


def get_fingerprint(pubkey: str) -> str:
    proc = Popen(["ssh-keygen", "-l", "-f", "-"], stdin=PIPE, stdout=PIPE,
                 stderr=PIPE)
    out, _ = proc.communicate(pubkey.encode())
    if proc.returncode:
        raise ValueError("The SSH public key is invalid.")
    return out.decode().split()[1].split(":", 1)[1]
