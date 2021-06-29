#!/bin/bash
set -eou pipefail

# Setup a config for our mysql db.
cp -vf conf/config.dev conf/config
sed -i "s;YOUR_AUR_ROOT;$(pwd);g" conf/config
sed -ri 's/^(host) = .+/\1 = mariadb/' conf/config
sed -ri 's/^(user) = .+/\1 = aur/' conf/config
sed -ri 's/^;?(password) = .+/\1 = aur/' conf/config

# Setup http(s) stuff.
sed -ri "s|^(aur_location) = .+|\1 = https://localhost:8444|" conf/config
sed -ri 's/^(disable_http_login) = .+/\1 = 1/' conf/config

cp -vf /cache/localhost.cert.pem /etc/ssl/certs/localhost.cert.pem
cp -vf /cache/localhost.key.pem /etc/ssl/private/localhost.key.pem

cp -vf /docker/config/nginx.conf /etc/nginx/nginx.conf

exec "$@"
