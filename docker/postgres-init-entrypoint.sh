#!/bin/bash
set -eou pipefail

# Setup a config for our postgres db via socket connection.
aurweb-config set database name 'aurweb'
aurweb-config set database user 'aur'
aurweb-config set database socket '/run/postgresql'
aurweb-config unset database host
aurweb-config unset database port
aurweb-config unset database password

exec "$@"
