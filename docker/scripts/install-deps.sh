#!/bin/bash
# Install Arch Linux dependencies. This is centralized here
# for CI and Docker usage and should always reflect the most
# robust development ecosystem.
set -eou pipefail

pacman-key --init
pacman-key -u
pacman-key --populate

# Install/update archlinux-keyring without cache.
pacman -Sy --noconfirm --noprogressbar archlinux-keyring

# Install/update Arch Linux dependencies.
pacman -Syu --noconfirm --noprogressbar \
    --cachedir .pkg-cache git gpgme nginx redis openssh \
      mariadb mariadb-libs cgit-aurweb uwsgi uwsgi-plugin-cgi \
      php php-fpm memcached php-memcached python-pip pyalpm \
      python-srcinfo curl libeatmydata cronie python-poetry \
      python-poetry-core step-cli step-ca asciidoc

exec "$@"
