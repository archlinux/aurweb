aurweb Test Collection
======================

To run all tests, you may run `make check` under `test/` (alternative targets:
`make pytest`, `make sh`).

For more control, you may use the `prove` or `pytest` command, which receives a
directory or a list of files to run, and produces a report.

Each test script is standalone, so you may run them individually. Some tests
may receive command-line options to help debugging. See for example sharness's
documentation for shell test scripts:
https://github.com/chriscool/sharness/blob/master/README.git

Dependencies
------------

For all the test to run, the following Arch packages should be installed:

- pyalpm
- python-alembic
- python-bleach
- python-markdown
- python-pygit2
- python-sqlalchemy
- python-srcinfo
- python-coverage
- python-pytest
- python-pytest-cov
- python-pytest-asyncio
- postfix
- openssh

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

Now, one must decide a database backend to use; see
[Test Database](#test-database) for details on configuring
the different supported backends.

Test Database
-------------

Users may choose to configure one of several backends, including:
`mysql` and `sqlite`. By default, `conf/config.dev` is configured
for a the `mysql` backend using a test database named `aurweb_test`.

Users can initialize an empty MySQL database by performing the following:

    $ cat conf/config
    [database]
    backend = mysql
    name = aurweb_test
    user = aur
    password = aur
    socket = /var/run/mysqld/mysqld.sock
    ...

    # mysql -u root -e "CREATE USER 'aur'@'localhost' IDENTIFIED BY 'aur'"
    # mysql -u root -e "CREATE DATABASE aurweb_test"
    # mysql -u root -e "GRANT ALL ON aurweb_test.* TO 'aur'@'localhost'"
    # mysql -u root -e "FLUSH ALL PRIVILEGES"

    $ export AUR_CONFIG=conf/config
    $ python3 -m aurweb.initdb

Or more lightweight with `sqlite`:

    $ cat $AUR_CONFIG
    [database]
    backend = sqlite
    name = aurweb.sqlite3
    ...

    $ export AUR_CONFIG=conf/config
    $ python3 -m aurweb.initdb

After initializing a fresh test database, users can continue on to
[Running Tests](#running-tests).

Running tests
-------------

Recommended method of running tests: `make check`.

Makefile test targets: `sh`, `pytest`.

Run tests from the project root.

    $ cd /path/to/aurweb

Ensure you have the proper `AUR_CONFIG` exported:

    $ export AUR_CONFIG=conf/config

To run `sharness` shell test suites (requires Arch Linux):

    $ make -C test sh

To run `pytest` Python test suites:

    $ make -C test pytest

To produce coverage reports related to Python when running tests manually,
use the following method:

    $ coverage run --append /path/to/python/file.py

**Note:** Sharness test suites (shell) internally run coverage run.

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

- `aurweb.testing.setup_init_db(*tables)`
    - Prepares test database tables to be cleared before a test
      is run. Be careful not to specify any tables we depend on
      for constant records, like `AccountTypes`, `DependencyTypes`,
      `RelationTypes` and `RequestTypes`.
- `aurweb.testing.requests.Request`
    - A fake stripped down version of `fastapi.Request` that can
      be passed to any functions in our codebase which use
      `fastapi.Request` parameters.

Example code:

    import pytest

    from aurweb import db
    from aurweb.models.user import User
    from aurweb.testing import setup_test_db
    from aurweb.testing.requests import Request


    @pytest.fixture(autouse=True)
    def setup():
        setup_test_db(User.__tablename__)

    @pytest.fixture
    def user():
        yield db.create(User, Passwd="testPassword", ...)

    def test_user_login(user):
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
