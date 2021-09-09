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

sed -ri "s;^(aur_location) = .+;\1 = https://localhost:8443;" conf/config

# Enable memcached.
sed -ri 's/^(cache) = .+$/\1 = memcache/' conf/config

sed -ri "s|^(git_clone_uri_anon) = .+|\1 = https://localhost:8443/%s.git|" conf/config.defaults
sed -ri "s|^(git_clone_uri_priv) = .+|\1 = ssh://aur@localhost:2222/%s.git|" conf/config.defaults

sed -ri 's/^(listen).*/\1 = 0.0.0.0:9000/' /etc/php/php-fpm.d/www.conf
sed -ri 's/^;?(clear_env).*/\1 = no/' /etc/php/php-fpm.d/www.conf

# Log to stderr. View logs via `docker-compose logs php-fpm`.
sed -ri 's|^(error_log) = .*$|\1 = /proc/self/fd/2|g' /etc/php/php-fpm.conf
sed -ri 's|^;?(access\.log) = .*$|\1 = /proc/self/fd/2|g' \
    /etc/php/php-fpm.d/www.conf

sed -ri 's/^;?(extension=pdo_mysql)/\1/' /etc/php/php.ini
sed -ri 's/^;?(open_basedir).*$/\1 = \//' /etc/php/php.ini

# Use the sqlite3 extension line for memcached.
sed -ri 's/^;(extension)=sqlite3$/\1=memcached/' /etc/php/php.ini

exec "$@"
