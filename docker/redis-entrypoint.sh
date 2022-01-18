#!/bin/bash
set -eou pipefail

sed -ri 's/^bind .*$/bind 0.0.0.0 -::1/g' /etc/redis/redis.conf

exec "$@"
