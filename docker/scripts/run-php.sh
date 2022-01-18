#!/bin/bash
set -eou pipefail

exec php-fpm --fpm-config /etc/php/php-fpm.conf --nodaemonize
