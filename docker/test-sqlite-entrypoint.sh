#!/bin/bash
set -eou pipefail

DB_BACKEND="sqlite"
DB_NAME="aurweb.sqlite3"

# Create an SQLite config from the default dev config.
cp -vf conf/config.dev conf/config.sqlite
cp -vf conf/config.defaults conf/config.sqlite.defaults

# Modify it for SQLite.
sed -i "s;YOUR_AUR_ROOT;$(pwd);g" conf/config.sqlite
sed -ri "s/^(backend) = .+/\1 = ${DB_BACKEND}/" conf/config.sqlite
sed -ri "s/^(name) = .+/\1 = ${DB_NAME}/" conf/config.sqlite

exec "$@"
