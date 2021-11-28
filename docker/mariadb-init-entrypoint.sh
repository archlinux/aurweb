#!/bin/bash
set -eou pipefail

# Setup a config for our mysql db.
aurweb-config set database name 'aurweb'
aurweb-config set database user 'aur'
aurweb-config set database password 'aur'
aurweb-config set database host 'localhost'
aurweb-config set database socket '/var/run/mysqld/mysqld.sock'
aurweb-config unset database port

if [ ! -z ${NO_INITDB+x} ]; then
    exec "$@"
fi

python -m aurweb.initdb 2>/dev/null || /bin/true
exec "$@"
