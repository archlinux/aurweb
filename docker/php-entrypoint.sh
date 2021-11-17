#!/bin/bash
set -eou pipefail

for archive in packages pkgbase users packages-meta-v1.json packages-meta-ext-v1.json; do
    ln -vsf /var/lib/aurweb/archives/${archive}.gz /aurweb/web/html/${archive}.gz
done

# Setup a config for our mysql db.
cp -vf conf/config.dev conf/config
sed -i "s;YOUR_AUR_ROOT;$(pwd);g" conf/config

# Change database user/password.
sed -ri "s/^;?(user) = .*$/\1 = aur/" conf/config
sed -ri "s/^;?(password) = .*$/\1 = aur/" conf/config

# Enable memcached.
sed -ri 's/^(cache) = .+$/\1 = memcache/' conf/config

# Setup various location configurations.
sed -ri "s;^(aur_location) = .+;\1 = ${AURWEB_PHP_PREFIX};" conf/config
sed -ri "s|^(git_clone_uri_anon) = .+|\1 = ${AURWEB_PHP_PREFIX}/%s.git|" conf/config.defaults
sed -ri "s|^(git_clone_uri_priv) = .+|\1 = ${AURWEB_SSHD_PREFIX}/%s.git|" conf/config.defaults

# Listen on :9000.
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
