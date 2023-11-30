#!/bin/bash
set -eou pipefail
dir="$(dirname $0)"

bash $dir/test-postgres-entrypoint.sh

exec "$@"
