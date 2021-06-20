#!/bin/bash
set -eou pipefail

mariadb-install-db --user=mysql --basedir=/usr --datadir=/var/lib/mysql

exec "$@"
