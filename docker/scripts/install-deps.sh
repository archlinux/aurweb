#!/bin/bash
# Install Arch Linux dependencies. This is centralized here
# for CI and Docker usage and should always reflect the most
# robust development ecosystem.
set -eou pipefail

pacman -Syu --noconfirm --noprogressbar \
    --cachedir .pkg-cache git gpgme protobuf pyalpm \
    python-mysqlclient python-pygit2 python-srcinfo python-bleach \
    python-markdown python-sqlalchemy python-alembic python-pytest \
    python-werkzeug python-pytest-tap python-fastapi nginx python-authlib \
    python-itsdangerous python-httpx python-jinja python-pytest-cov \
    python-requests python-aiofiles python-python-multipart \
    python-pytest-asyncio python-coverage hypercorn python-bcrypt \
    python-email-validator openssh python-lxml mariadb mariadb-libs \
    python-isort flake8 cgit uwsgi uwsgi-plugin-cgi php php-fpm \
    python-asgiref uvicorn python-feedgen memcached php-memcached \
    python-redis redis

exec "$@"
