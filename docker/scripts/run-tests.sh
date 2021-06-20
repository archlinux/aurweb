#!/bin/bash
set -eou pipefail
dir=$(dirname $0)

# Clean up coverage and stuff.
make -C test clean

# Run sharness tests.
bash $dir/run-sharness.sh

# Run Python tests with MariaDB database.
# Pass --silence to avoid reporting coverage. We will do that below.
bash $dir/run-pytests.sh --no-coverage

# Export SQLite aurweb configuration.
export AUR_CONFIG=conf/config.sqlite

# Run Python tests.
bash $dir/run-pytests.sh --no-coverage

make -C test coverage

# /cache is mounted as a volume. Copy coverage into it.
# Users can then sanitize the coverage locally in their
# aurweb root directory: ./util/fix-coverage ./cache/.coverage
rm -f /cache/.coverage
cp -v .coverage /cache/.coverage
chmod 666 /cache/.coverage

# Run flake8 and isort checks.
for dir in aurweb test migrations; do
    flake8 --count $dir
    isort --check-only $dir
done
