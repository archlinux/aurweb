#!/bin/bash
set -eou pipefail

# Setup the DB.
NO_INITDB=1 /docker/mariadb-init-entrypoint.sh

# Create aurblup's directory.
AURBLUP_DIR="/aurweb/aurblup/"
mkdir -p $AURBLUP_DIR

# Setup aurblup config for Docker.
AURBLUP_DBS='core extra multilib core-testing extra-testing multilib-testing'
AURBLUP_SERVER='https://mirrors.kernel.org/archlinux/%s/os/x86_64'
aurweb-config set aurblup db-path "$AURBLUP_DIR"
aurweb-config set aurblup sync-dbs "$AURBLUP_DBS"
aurweb-config set aurblup server "$AURBLUP_SERVER"

# Setup mkpkglists config for Docker.
ARCHIVE_DIR='/var/lib/aurweb/archives'
aurweb-config set mkpkglists archivedir "$ARCHIVE_DIR"
aurweb-config set mkpkglists packagesfile "$ARCHIVE_DIR/packages.gz"
aurweb-config set mkpkglists packagesmetafile \
    "$ARCHIVE_DIR/packages-meta-v1.json.gz"
aurweb-config set mkpkglists packagesmetaextfile \
    "$ARCHIVE_DIR/packages-meta-ext-v1.json.gz"
aurweb-config set mkpkglists pkgbasefile "$ARCHIVE_DIR/pkgbase.gz"
aurweb-config set mkpkglists userfile "$ARCHIVE_DIR/users.gz"

# Install the cron configuration.
cp /docker/config/aurweb-cron /etc/cron.d/aurweb-cron
chmod 0644 /etc/cron.d/aurweb-cron
crontab /etc/cron.d/aurweb-cron

exec "$@"
