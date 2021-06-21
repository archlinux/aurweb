#!/bin/bash
set -eou pipefail
dir="$(dirname $0)"

bash $dir/test-mysql-entrypoint.sh

sed -ri "s;^(aur_location) = .+;\1 = https://localhost:8443;" conf/config
sed -ri 's/^(name) = .+/\1 = aurweb/' conf/config

sed -ri 's/^(listen).*/\1 = 0.0.0.0:9000/' /etc/php/php-fpm.d/www.conf
sed -ri 's/^;?(clear_env).*/\1 = no/' /etc/php/php-fpm.d/www.conf

sed -ri 's/^;?(extension=pdo_mysql)/\1/' /etc/php/php.ini
sed -ri 's/^;?(open_basedir).*$/\1 = \//' /etc/php/php.ini

python -m aurweb.initdb 2>/dev/null || /bin/true

exec "$@"
