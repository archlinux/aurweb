# Contributing

Patches should be sent to the [aur-dev@lists.archlinux.org][1] mailing list
or included in a merge request on the [aurweb repository][2].

Before sending patches, you are recommended to run `flake8` and `isort`.

You can add a git hook to do this by installing `python-pre-commit` and running
`pre-commit install`.

[1]: https://lists.archlinux.org/listinfo/aur-dev
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

We use the `flake8` and `isort` tools to manage PEP-8 coherenace and
import ordering in this project.

There are plugins for editors or IDEs which automate this process. Some
example plugins:

- [tell-k/vim-autopep8](https://github.com/tell-k/vim-autopep8)
- [fisadev/vim-isort](https://github.com/fisadev/vim-isort)
- [prabirshrestha/vim-lsp](https://github.com/prabirshrestha/vim-lsp)

See `setup.cfg` for flake8 and isort specific rules.

Note: We are planning on switching to [psf/black](https://github.com/psf/black).
For now, developers should ensure that flake8 and isort passes when submitting
merge requests or patch sets.

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
