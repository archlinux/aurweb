#!/bin/bash
set -eou pipefail

[[ -z "$DB_HOST" ]] && echo 'Error: $DB_HOST required but missing.' && exit 1

DB_NAME="aurweb"
DB_USER="aur"
DB_PASS="aur"

# Setup a config for our mysql db.
cp -vf conf/config.dev conf/config
sed -i "s;YOUR_AUR_ROOT;$(pwd);g" conf/config
sed -ri "s/^(name) = .+/\1 = ${DB_NAME}/" conf/config
sed -ri "s/^(host) = .+/\1 = ${DB_HOST}/" conf/config
sed -ri "s/^(user) = .+/\1 = ${DB_USER}/" conf/config
sed -ri "s/^;?(password) = .+/\1 = ${DB_PASS}/" conf/config

python -m aurweb.initdb 2>/dev/null || /bin/true

exec "$@"
