#!/bin/bash
# Install Arch Linux dependencies. This is centralized here
# for CI and Docker usage and should always reflect the most
# robust development ecosystem.
set -eou pipefail

# Update and rollout archlinux-keyring keys.
pacman-key --init
pacman-key --updatedb
pacman-key --populate

pacman -Sy --noconfirm --noprogressbar archlinux-keyring

# Install other OS dependencies.
pacman -Syu --noconfirm --noprogressbar \
    git gpgme nginx valkey openssh \
    mariadb mariadb-libs cgit-aurweb uwsgi uwsgi-plugin-cgi \
    python-pip pyalpm python-srcinfo python-alpm curl libeatmydata cronie \
    python-poetry python-poetry-core step-cli step-ca asciidoc \
    python-virtualenv python-pre-commit

exec "$@"
