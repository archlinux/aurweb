import io
from subprocess import PIPE, Popen

import pytest

from aurweb import config
from aurweb.testing.email import Email


@pytest.fixture(autouse=True)
def setup(email_test):
    return


def sendmail(from_: str, to_: str, content: str) -> Email:
    binary = config.get("notifications", "sendmail")
    proc = Popen(binary, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    content = f"From: {from_}\nTo: {to_}\n\n{content}"
    proc.communicate(content.encode())
    proc.wait()
    assert proc.returncode == 0


def test_email_glue():
    """Test that Email.glue() decodes both base64 and decoded content."""
    body = "Test email."
    sendmail("test@example.org", "test@example.org", body)
    assert Email.count() == 1

    email1 = Email(1)
    email2 = Email(1)
    assert email1.glue() == email2.glue()


def test_email_dump():
    """Test that Email.dump() dumps a single email."""
    body = "Test email."
    sendmail("test@example.org", "test@example.org", body)
    assert Email.count() == 1

    stdout = io.StringIO()
    Email.dump(file=stdout)
    content = stdout.getvalue()
    assert "== Email #1 ==" in content


def test_email_dump_multiple():
    """Test that Email.dump() dumps multiple emails."""
    body = "Test email."
    sendmail("test@example.org", "test@example.org", body)
    sendmail("test2@example.org", "test2@example.org", body)
    assert Email.count() == 2

    stdout = io.StringIO()
    Email.dump(file=stdout)
    content = stdout.getvalue()
    assert "== Email #1 ==" in content
    assert "== Email #2 ==" in content
