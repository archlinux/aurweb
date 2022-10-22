# Contributing

Patches should be sent to the [aur-dev@lists.archlinux.org][1] mailing list
or included in a merge request on the [aurweb repository][2].

Before sending patches, you are recommended to run `flake8` and `isort`.

You can add a git hook to do this by installing `python-pre-commit` and running
`pre-commit install`.

[1]: https://lists.archlinux.org/mailman3/lists/aur-dev.lists.archlinux.org/
[2]: https://gitlab.archlinux.org/archlinux/aurweb

### Coding Guidelines

DISCLAIMER: We realise the code doesn't necessarily follow all the rules.
This is an attempt to establish a standard coding style for future
development.

1. All source modified or added within a patchset **must** maintain equivalent
   or increased coverage by providing tests that use the functionality
2. Please keep your source within an 80 column width
3. Use four space indentation
4. Use [conventional commits](https://www.conventionalcommits.org/en/v1.0.0/)
5. DRY: Don't Repeat Yourself
6. All code should be tested for good _and_ bad cases (see [test/README.md][3])

[3]: https://gitlab.archlinux.org/archlinux/aurweb/-/blob/master/test/README.md

Test patches that increase coverage in the codebase are always welcome.

### Coding Style

We use `autoflake`, `isort`, `black` and `flake8` to enforce coding style in a
PEP-8 compliant way. These tools run in GitLab CI using `pre-commit` to verify
that any pushed code changes comply with this.

To enable the `pre-commit` git hook, install the `pre-commit` package either
with `pacman` or `pip` and then run `pre-commit install --install-hooks`. This
will ensure formatting is done before any code is commited to the git
repository.

There are plugins for editors or IDEs which automate this process. Some
example plugins:

- [tenfyzhong/autoflake.vim](https://github.com/tenfyzhong/autoflake.vim)
- [fisadev/vim-isort](https://github.com/fisadev/vim-isort)
- [psf/black](https://github.com/psf/black)
- [nvie/vim-flake8](https://github.com/nvie/vim-flake8)
- [prabirshrestha/vim-lsp](https://github.com/prabirshrestha/vim-lsp)
- [dense-analysis/ale](https://github.com/dense-analysis/ale)

See `setup.cfg`, `pyproject.toml` and `.pre-commit-config.yaml` for tool
specific configurations.

### Development Environment

To get started with local development, an instance of aurweb must be
brought up. This can be done using the following sections:

- [Using Docker](#using-docker)
- [Using INSTALL](#using-install)

There are a number of services aurweb employs to run the application
in its entirety:

- ssh
- cron jobs
- starlette/fastapi asgi server

Project structure:

- `./aurweb`: `aurweb` Python package
- `./templates`: Jinja2 templates
- `./docker`: Docker scripts and configuration files

#### Using Docker

Using Docker, we can run the entire infrastructure in two steps:

    # Build the aurweb:latest image
    $ docker-compose build

    # Start all services in the background
    $ docker-compose up -d nginx

`docker-compose` services will generate a locally signed root certificate
at `./data/root_ca.crt`. Users can import this into ca-certificates or their
browser if desired.

Accessible services (on the host):

- https://localhost:8444 (python via nginx)
- https://localhost:8443 (php via nginx)
- localhost:13306 (mariadb)
- localhost:16379 (redis)

Docker services, by default, are setup to be hot reloaded when source code
is changed.

#### Using INSTALL

The [INSTALL](INSTALL) file describes steps to install the application on
bare-metal systems.
