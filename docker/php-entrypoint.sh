#!/bin/bash
set -eou pipefail
dir="$(dirname $0)"

bash $dir/test-mysql-entrypoint.sh

sed -ri "s;^(aur_location) = .+;\1 = https://localhost:8443;" conf/config
sed -ri 's/^(name) = .+/\1 = aurweb/' conf/config

sed -ri "s|^(git_clone_uri_anon) = .+|\1 = https://localhost:8443/cgit/aur.git -b %s|" conf/config.defaults
sed -ri "s|^(git_clone_uri_priv) = .+|\1 = ssh://aur@localhost:2222/%s.git|" conf/config.defaults

sed -ri 's/^(listen).*/\1 = 0.0.0.0:9000/' /etc/php/php-fpm.d/www.conf
sed -ri 's/^;?(clear_env).*/\1 = no/' /etc/php/php-fpm.d/www.conf

# Log to stderr. View logs via `docker-compose logs php-fpm`.
sed -ri 's|^(error_log) = .*$|\1 = /proc/self/fd/2|g' /etc/php/php-fpm.conf
sed -ri 's|^;?(access\.log) = .*$|\1 = /proc/self/fd/2|g' \
    /etc/php/php-fpm.d/www.conf

sed -ri 's/^;?(extension=pdo_mysql)/\1/' /etc/php/php.ini
sed -ri 's/^;?(open_basedir).*$/\1 = \//' /etc/php/php.ini

python -m aurweb.initdb 2>/dev/null || /bin/true

exec "$@"
