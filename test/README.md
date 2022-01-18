aurweb Test Collection
======================

To run all tests, you may run `make -C test sh` and `pytest` within
the project root:

    $ make -C test sh    # Run Sharness tests.
    $ poetry run pytest  # Run Pytest suites.

For more control, you may use the `prove` or `pytest` command, which receives a
directory or a list of files to run, and produces a report.

Each test script is standalone, so you may run them individually. Some tests
may receive command-line options to help debugging.

Dependencies
------------

For all tests to run dependencies provided via `poetry` are required:

    $ poetry install

Logging
-------

Tests also require the `logging.test.conf` logging configuration
file to be used. You can specify the `LOG_CONFIG` environment
variable to override:

    $ export LOG_CONFIG=logging.test.conf

`logging.test.conf` enables debug logging for the aurweb package,
for which we run tests against.

Test Configuration
------------------

To perform any tests, we need to supply `aurweb` with a valid
configuration. For development (and testing) purposes, an example
[conf/config.dev](../conf/config.dev) can be slightly modified.

Start off by copying `config.dev` to a new configuration.

    $ cp -v conf/config.dev conf/config

First, we must tell `aurweb` where the root of our project
lives by replacing `YOUR_AUR_ROOT` with the path to the aurweb
repository.

    $ sed -i "s;YOUR_AUR_ROOT;/path/to/aurweb;g" conf/config

Test Databases
--------------

Python tests create and drop hashed database names based on
`PYTEST_CURRENT_TEST`. To run tests with a database, the database
user must have privileges to create and drop their own databases.
Typically, this is the root user, but can be configured for any
other user:

    GRANT ALL ON *.* TO 'user'@'localhost' WITH GRANT OPTION

The aurweb platform is intended to use the `mysql` backend, but
the `sqlite` backend is still used for sharness tests. These tests
will soon be replaced with pytest suites and `sqlite` removed.

After ensuring you've configured a test database, users can continue
on to [Running Tests](#running-tests).

Running tests
-------------

Makefile test targets: `sh`, `clean`.

Recommended method of running tests: `pytest`.

Legacy sharness tests: `make -C test sh`.

aurweb is currently going through a refactor where  the majority of
`sharness` tests have been replaced with `pytest` units. There are
still a few `sharness` tests around, and they are required to gain
as much coverage as possible over an entire test run. Users should
be writing `pytest` units for any new features.

Run tests from the project root.

    $ cd /path/to/aurweb

Ensure you have the proper `AUR_CONFIG` and `LOG_CONFIG` exported:

    $ export AUR_CONFIG=conf/config
    $ export LOG_CONFIG=logging.test.conf

To run `sharness` shell test suites (requires Arch Linux):

    $ make -C test sh

To run `pytest` Python test suites:

    # With poetry-installed aurweb
    $ poetry run pytest

    # With globally-installed aurweb
    $ pytest

After tests are run, one can produce coverage reports.

    # Print out a CLI coverage report.
    $ coverage report

    # Produce an HTML-based coverage report.
    $ coverage html

Writing Python tests (current)
------------------------------

Almost all of our `pytest` suites use the database in some way. There
are a few particular testing utilities in `aurweb` that one should
keep aware of to aid testing code:

- `db_test` pytest fixture
    - Prepares test databases for the module and cleans out database
      tables for each test function requiring this fixture.
- `aurweb.testing.requests.Request`
    - A fake stripped down version of `fastapi.Request` that can
      be passed to any functions in our codebase which use
      `fastapi.Request` parameters.

Example code:

    import pytest

    from aurweb import db
    from aurweb.models.account_type import USER_ID
    from aurweb.models.user import User
    from aurweb.testing.requests import Request

    # We need to use the `db_test` fixture at some point
    # during our test functions.
    @pytest.fixture(autouse=True)
    def setup(db_test: None) -> None:
        return

    # Or... specify it in a dependency fixture.
    @pytest.fixture
    def user(db_test: None) -> User:
        with db.begin():
            user = db.create(User, Username="test",
                             Email="test@example.org",
                             Passwd="testPassword",
                             AccountTypeID=USER_ID)
        yield user

    def test_user_login(user: User):
        assert isinstance(user, User) is True

        fake_request = Request()
        sid = user.login(fake_request, "testPassword")
        assert sid is not None

Writing Sharness tests (legacy)
-------------------------------

Shell test scripts must follow the Test Anything Protocol specification:
http://testanything.org/tap-specification.html

Python tests must be compatible with `pytest` and included in `pytest test/`
execution after setting up a configuration.

Tests must support being run from any directory. They may use $0 to determine
their location. Python scripts should expect aurweb to be installed and
importable without toying with os.path or PYTHONPATH.

Tests written in shell should use sharness. In general, new tests should be
consistent with existing tests unless they have a good reason not to.

Debugging Sharness tests
---------------

By default, `make -C test` is quiet and does not print out verbose information
about tests being run. If a test is failing, one can look into verbose details
of sharness tests by executing them with the `--verbose` flag. Example:
`./t1100_git_auth.t --verbose`. This is particularly useful when tests happen
to fail in a remote continuous integration environment, where the reader does
not have complete access to the runner.
