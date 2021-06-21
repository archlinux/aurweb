#!/bin/bash
set -eou pipefail

# Initialize the new database; ignore errors.
python -m aurweb.initdb 2>/dev/null || /bin/true

exec php-fpm --fpm-config /etc/php/php-fpm.conf --nodaemonize
