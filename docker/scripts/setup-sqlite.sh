#!/bin/bash
# Run an sqlite test. This script really just prepares sqlite
# tests by deleting any existing databases so the test can
# initialize cleanly.
DB_NAME="$(grep 'name =' conf/config.sqlite | sed -r 's/^name = (.+)$/\1/')"
rm -vf $DB_NAME
exec "$@"
