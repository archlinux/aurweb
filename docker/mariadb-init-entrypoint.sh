#!/bin/bash
set -eou pipefail

# Setup a config for our mysql db.
cp -vf conf/config.dev conf/config
sed -i "s;YOUR_AUR_ROOT;$(pwd);g" conf/config
sed -ri "s/^;?(user) = .*$/\1 = aur/g" conf/config
sed -ri "s/^;?(password) = .*$/\1 = aur/g" conf/config

python -m aurweb.initdb 2>/dev/null || /bin/true

exec "$@"
