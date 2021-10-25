#!/bin/bash
set -eou pipefail

# Setup a config for our mysql db.
cp -vf conf/config.dev conf/config
sed -i "s;YOUR_AUR_ROOT;$(pwd);g" conf/config

sed -ri "s;^(aur_location) = .+;\1 = ${AURWEB_FASTAPI_PREFIX};" conf/config

# Setup Redis for FastAPI.
sed -ri 's/^(cache) = .+/\1 = redis/' conf/config
sed -ri 's|^(redis_address) = .+|\1 = redis://redis|' conf/config

sed -ri "s|^(git_clone_uri_anon) = .+|\1 = ${AURWEB_FASTAPI_PREFIX}/%s.git|" conf/config.defaults
sed -ri "s|^(git_clone_uri_priv) = .+|\1 = ${AURWEB_SSHD_PREFIX}/%s.git|" conf/config.defaults

exec "$@"
