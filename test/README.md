Running tests
-------------

To run all tests, you may run `make check` under `test/` (alternative targets:
`make pytest`, `make sh`).

For more control, you may use the `prove` or `pytest` command, which receives a
directory or a list of files to run, and produces a report.

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
- python-coverage
- python-pytest
- python-pytest-cov
- python-pytest-asyncio

Running tests
-------------

Recommended method of running tests: `make check`.

First, setup the test configuration:

    $ sed -r 's;YOUR_AUR_ROOT;$(pwd);g' conf/config.dev > conf/config

With those installed, one can run Python tests manually with any AUR config
specified by `AUR_CONFIG`:

    $ AUR_CONFIG=conf/config coverage run --append /usr/bin/pytest test/

After tests are run (particularly, with `coverage run` included), one can
produce coverage reports.

    # Print out a CLI coverage report.
    $ coverage report
    # Produce an HTML-based coverage report.
    $ coverage html

When running `make -C test`, all tests ran will produce coverage data via
`coverage run --append`. After running `make -C test`, one can continue with
coverage reporting steps above. Running tests through `make` will test and
cover code ran by both aurweb scripts and our pytest collection.

Writing tests
-------------

Shell test scripts must follow the Test Anything Protocol specification:
http://testanything.org/tap-specification.html

Python tests must be compatible with `pytest` and included in `pytest test/`
execution after setting up a configuration.

Tests must support being run from any directory. They may use $0 to determine
their location. Python scripts should expect aurweb to be installed and
importable without toying with os.path or PYTHONPATH.

Tests written in shell should use sharness. In general, new tests should be
consistent with existing tests unless they have a good reason not to.

Debugging tests
---------------

By default, `make -C test` is quiet and does not print out verbose information
about tests being run. If a test is failing, one can look into verbose details
of sharness tests by executing them with the `--verbose` flag. Example:
`./t1100_git_auth.t --verbose`. This is particularly useful when tests happen
to fail in a remote continuous integration environment, where the reader does
not have complete access to the runner.
