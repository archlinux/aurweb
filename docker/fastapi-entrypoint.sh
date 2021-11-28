#!/bin/bash
set -eou pipefail

# Setup a config for our mysql db.
cp -vf conf/config.dev conf/config
sed -i "s;YOUR_AUR_ROOT;$(pwd);g" conf/config

# Setup database.
aurweb-config set database user 'aur'
aurweb-config set database password 'aur'
aurweb-config set database host 'localhost'
aurweb-config set database socket '/var/lib/mysqld/mysqld.sock'
aurweb-config unset database port

# Setup some other options.
aurweb-config set options cache 'redis'
aurweb-config set options redis_address 'redis://redis'
aurweb-config set options aur_location "$AURWEB_FASTAPI_PREFIX"
aurweb-config set options git_clone_uri_anon "${AURWEB_FASTAPI_PREFIX}/%s.git"
aurweb-config set options git_clone_uri_priv "${AURWEB_SSHD_PREFIX}/%s.git"

if [ ! -z ${COMMIT_HASH+x} ]; then
    aurweb-config set devel commit_hash "$COMMIT_HASH"
fi

# Setup prometheus directory.
rm -rf $PROMETHEUS_MULTIPROC_DIR
mkdir -p $PROMETHEUS_MULTIPROC_DIR

exec "$@"
