#!/bin/bash
set -eou pipefail
dir="$(dirname $0)"

bash $dir/test-mysql-entrypoint.sh

sed -ri "s;^(aur_location) = .+;\1 = https://localhost:8444;" conf/config
sed -ri 's/^(name) = .+/\1 = aurweb/' conf/config

exec "$@"
