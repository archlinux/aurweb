#!/bin/bash
set -eou pipefail
dir=$(dirname $0)

# Clean up coverage and stuff.
make -C test clean

# Run sharness tests.
bash $dir/run-sharness.sh

# Run Python tests with PostgreSQL database.
# Pass --silence to avoid reporting coverage. We will do that below.
bash $dir/run-pytests.sh --no-coverage

make -C test coverage

# /data is mounted as a volume. Copy coverage into it.
# Users can then sanitize the coverage locally in their
# aurweb root directory: ./util/fix-coverage ./data/.coverage
rm -f /data/.coverage
cp -v .coverage /data/.coverage
chmod 666 /data/.coverage

# Run pre-commit checks
pre-commit run -a
