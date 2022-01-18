#!/bin/bash
set -eou pipefail
dir="$(dirname $0)"

bash $dir/test-mysql-entrypoint.sh

exec "$@"
