#!/bin/bash
set -eou pipefail

sed -ri 's/^bind .*$/bind 0.0.0.0 -::1/g' /etc/valkey/valkey.conf
sed -ri 's/protected-mode yes/protected-mode no/g' /etc/valkey/valkey.conf

exec "$@"
