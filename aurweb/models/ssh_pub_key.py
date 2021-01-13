import os
import tempfile

from subprocess import PIPE, Popen

from sqlalchemy.orm import backref, mapper, relationship

from aurweb.models.user import User
from aurweb.schema import SSHPubKeys


class SSHPubKey:
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


mapper(SSHPubKey, SSHPubKeys, properties={
    "User": relationship(User, backref=backref("ssh_pub_key", uselist=False))
})
