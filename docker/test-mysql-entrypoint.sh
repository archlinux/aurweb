#!/bin/bash
set -eou pipefail

DB_NAME="aurweb_test"

# Setup a config for our mysql db.
cp -vf conf/config.dev conf/config
sed -i "s;YOUR_AUR_ROOT;$(pwd);g" conf/config
sed -ri "s/^(name) = .+/\1 = ${DB_NAME}/" conf/config

# The port can be excluded from use if properly using
# volumes to share the mysql socket from the mariadb service.
# Example port sed:
# sed -i "s/^;?(port = .+)$/\1/" conf/config

# Continue onto the main command.
exec "$@"
