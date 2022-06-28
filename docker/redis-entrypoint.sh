#!/bin/bash
set -eou pipefail

sed -ri 's/^bind .*$/bind 0.0.0.0 -::1/g' /etc/redis/redis.conf
sed -ri 's/protected-mode yes/protected-mode no/g' /etc/redis/redis.conf

exec "$@"
