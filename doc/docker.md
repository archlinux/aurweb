Table of Contents
-----------------

<table style="width: auto">
    <tbody>
        <tr>
            <td><a href="#getting-started">Getting Started</a></td>
            <td><a href="#profiles">Profiles</a></td>
            <td><a href="#services">Services</a></td>
        </tr>
    </tbody>
</table>

**Note:** The `docker-compose` infrastructure is experimental and
in need of improvements.

Getting Started
---------------

Install required dependencies:

    # pacman -Syu docker-compose

See [Profiles](#profiles) for details about using the different profiles
setup for aurweb. The following examples use the [default](#default) profile.

Begin by building `aurweb:latest` off the current revision:

    $ docker-compose build

You can run tests:

    $ docker-compose run test

Or, start the development server:

    $ docker-compose up -d nginx

See [nginx](#nginx) for details on connecting to the local instance.

Profiles
--------

| Name    | Options              |
|---------|----------------------|
| default | `docker-compose ...` |
| aur-dev | `docker-compose -f docker-compose.yml -f docker-compose.aur-dev.yml ...` |

#### default

Default development profile intended to be used on local systems.

#### aur-dev

Production profile used for deployments to
[aur-dev.archlinux.org](https://aur-dev.archlinux.org).

Services
--------

| Service             | Host Binding    |
|---------------------|-----------------|
| [ca](#ca)           |                 |
| [cron](#cron)       |                 |
| [mariadb](#mariadb) | 127.0.0.1:13306 |
| [git](#git)         | 127.0.0.1:2222  |
| redis               | 127.0.0.1:16379 |
| [fastapi](#fastapi) | 127.0.0.1:18000 |
| cgit-fastapi        |                 |
| [nginx](#nginx) (fastapi) | 127.0.0.1:8444  |

There are more services which have not been referred to here;
the services listed above encompass all notable services. Some
services have their own section, defined below, which lie down
specifics.

#### ca

The _ca_ service provides a certificate authority driven by `step-ca`.
When no certificates can be found, the ca services self-signs a new
root ca certificate and a localhost certificate to be used by nginx.

The generated root ca certificate, after generation, will be located
at `./data/root_ca.crt` and can be imported into ca_certificates
anchors or browsers for SSL verification.

#### cron

The _cron_ service includes all scripts recommended in `doc/maintenance.txt`.

#### mariadb

- When used with the [default](#default) profile, a Docker-driven
  mariadb service is used.
- When used with the [aur-dev](#aur-dev) profile, `MARIADB_SOCKET_DIR`
  (defaulted to `/var/run/mysqld/`) can be defined to bind-mount a
  host-driven mariadb socket to the container.

#### git

The _git_ service provides an ssh interface to a repository configured
to be used for the AUR.

- When used with the [default](#default) profile, a Docker-driven
  volume is used to manage the repository.
- When used with the [aur-dev](#aur-dev) profile, `GIT_DATA_DIR`
  should be set to a directory found on the host to be used for
  a bind-mounted repository.

This service will perform setup in either case if the repository
is not yet initialized.

#### fastapi

The _fastapi_ service hosts a `gunicorn`, `uvicorn` or `hypercorn`
asgi server. The backend and worker count can be configured using
the following variables:

- `FASTAPI_BACKEND`
    - Default: `uvicorn`
    - Valid: `gunicorn`, `uvicorn`, `hypercorn`
- `FASTAPI_WORKERS`
    - Default: 2

Additionally, when running any services which use the fastapi
backend or other fastapi-related services, users should define:

- `AURWEB_FASTAPI_PREFIX`
    - Default: `https://localhost:8444`
- `AURWEB_SSHD_PREFIX`
    - Default: `ssh://aur@localhost:2222`

#### nginx

The _nginx_ service binds to host endpoint: 127.0.0.1:8444 (fastapi).
The instance is available over the `https`
protocol as noted in the table below.

| Impl   | Host Binding   | URL                    |
|--------|----------------|------------------------|
| Python | 127.0.0.1:8444 | https://localhost:8444 |

When running this service, the following variables should be defined:

- `AURWEB_FASTAPI_PREFIX`
    - Default: `https://localhost:8444`
- `AURWEB_SSHD_PREFIX`
    - Default: `ssh://aur@localhost:2222`
