Running tests
-------------

To run all the tests, you may run `make check` under `test/`.

For more control, you may use the `prove` command, which receives a directory
or a list of files to run, and produces a report.

Each test script is standalone, so you may run them individually. Some tests
may receive command-line options to help debugging. See for example sharness's
documentation for shell test scripts:
https://github.com/chriscool/sharness/blob/master/README.git

### Dependencies

For all the test to run, the following Arch packages should be installed:

- pyalpm
- python-alembic
- python-bleach
- python-markdown
- python-pygit2
- python-sqlalchemy
- python-srcinfo

Writing tests
-------------

Test scripts must follow the Test Anything Protocol specification:
http://testanything.org/tap-specification.html

Tests must support being run from any directory. They may use $0 to determine
their location. Python scripts should expect aurweb to be installed and
importable without toying with os.path or PYTHONPATH.

Tests written in shell should use sharness. In general, new tests should be
consistent with existing tests unless they have a good reason not to.
