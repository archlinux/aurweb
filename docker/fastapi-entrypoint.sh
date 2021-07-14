#!/bin/bash
set -eou pipefail
dir="$(dirname $0)"

bash $dir/test-mysql-entrypoint.sh

sed -ri "s;^(aur_location) = .+;\1 = https://localhost:8444;" conf/config
sed -ri 's/^(name) = .+/\1 = aurweb/' conf/config

sed -ri "s|^(git_clone_uri_anon) = .+|\1 = https://localhost:8444/%s.git|" conf/config.defaults
sed -ri "s|^(git_clone_uri_priv) = .+|\1 = ssh://aur@localhost:2222/%s.git|" conf/config.defaults

exec "$@"
