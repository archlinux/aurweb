#!/bin/bash
set -eou pipefail

# Setup a config for our mysql db.
cp -vf conf/config.dev conf/config
sed -i "s;YOUR_AUR_ROOT;$(pwd);g" conf/config

aurweb-config set database user 'aur'
aurweb-config set database password 'aur'

python -m aurweb.initdb 2>/dev/null || /bin/true

exec "$@"
