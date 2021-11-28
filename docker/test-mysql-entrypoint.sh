#!/bin/bash
set -eou pipefail

# We use the root user for testing in Docker.
# The test user must be able to create databases and drop them.
aurweb-config set database user 'root'
aurweb-config set database host 'localhost'
aurweb-config set database socket '/var/run/mysqld/mysqld.sock'

# Remove possibly problematic configuration options.
# We depend on the database socket within Docker and
# being run as the root user.
aurweb-config unset database password
aurweb-config unset database port

exec "$@"
