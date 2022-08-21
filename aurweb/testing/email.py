import base64
import binascii
import copy
import email
import os
import re
import sys
from typing import TextIO


class Email:
    """
    An email class used for testing.

    This class targets a specific serial of emails for PYTEST_CURRENT_TEST.
    As emails are sent out with util/sendmail, the serial number increases,
    starting at 1.

    Email content sent out by aurweb is always base64-encoded. Email.parse()
    decodes that for us and puts it into Email.body.

    Example:

        # Get the {test_suite}_{test_function}.1.txt email.
        email = Email(1).parse()
        print(email.body)
        print(email.headers)

    """

    TEST_DIR = "test-emails"

    def __init__(self, serial: int = 1, autoparse: bool = True):
        self.serial = serial
        self.content = self._get()

        if autoparse:
            self._parse()

    @staticmethod
    def reset() -> None:
        # Cleanup all email files for this test suite.
        prefix = Email.email_prefix(suite=True)
        files = os.listdir(Email.TEST_DIR)
        for file in files:
            if file.startswith(prefix):
                os.remove(os.path.join(Email.TEST_DIR, file))

    @staticmethod
    def email_prefix(suite: bool = False) -> str:
        """
        Get the email prefix.

        We find the email prefix by reducing PYTEST_CURRENT_TEST to
        either {test_suite}_{test_function}. If `suite` is set, we
        reduce it to {test_suite} only.

        :param suite: Reduce PYTEST_CURRENT_TEST to {test_suite}
        :return: Email prefix with '/', '.', ',', and ':' chars replaced by '_'
        """
        value = os.environ.get("PYTEST_CURRENT_TEST", "email").split(" ")[0]
        if suite:
            value = value.split(":")[0]
        return re.sub(r"(\/|\.|,|:)", "_", value)

    @staticmethod
    def count() -> int:
        """
        Count the current number of emails sent from the test.

        This function is **only** supported inside of pytest functions.
        Do not use it elsewhere as data races will occur.

        :return: Number of emails sent by the current test
        """
        files = os.listdir(Email.TEST_DIR)
        prefix = Email.email_prefix()
        expr = "^" + prefix + r"\.\d+\.txt$"
        subset = filter(lambda e: re.match(expr, e), files)
        return len(list(subset))

    def _email_path(self) -> str:
        filename = self.email_prefix() + f".{self.serial}.txt"
        return os.path.join(Email.TEST_DIR, filename)

    def _get(self) -> str:
        """
        Get this email's content by reading its file.

        :return: Email content
        """
        path = self._email_path()
        with open(path) as f:
            return f.read()

    def _parse(self) -> "Email":
        """
        Parse this email and base64-decode the body.

        This function populates Email.message, Email.headers and Email.body.

        Additionally, after parsing, we write over our email file with
        self.glue()'d content (base64-decoded). This is done for ease
        of inspection by users.

        :return: self
        """
        self.message = email.message_from_string(self.content)
        self.headers = dict(self.message)

        # aurweb email notifications always have base64 encoded content.
        # Decode it here so self.body is human readable.
        try:
            self.body = base64.b64decode(self.message.get_payload()).decode()
        except (binascii.Error, UnicodeDecodeError):
            self.body = self.message.get_payload()

        path = self._email_path()
        with open(path, "w") as f:
            f.write(self.glue())

        return self

    def parse(self) -> "Email":
        return self

    def glue(self) -> str:
        """
        Glue parsed content back into a complete email document, but
        base64-decoded this time.

        :return: Email document as a string
        """
        headers = copy.copy(self.headers)

        if "Content-Transfer-Encoding" in headers:
            headers.pop("Content-Transfer-Encoding")

        output = []
        for k, v in headers.items():
            output.append(f"{k}: {v}")
        output.append("")
        output.append(self.body)
        return "\n".join(output)

    @staticmethod
    def dump(file: TextIO = sys.stdout) -> None:
        """
        Dump emails content to `file`.

        This function is intended to be used to debug email issues
        while testing something relevent to email.

        :param file: Writable file object
        """
        lines = []
        for i in range(Email.count()):
            email = Email(i + 1)
            lines += [
                f"== Email #{i + 1} ==",
                email.glue(),
                f"== End of Email #{i + 1}",
            ]
        print("\n".join(lines), file=file)
