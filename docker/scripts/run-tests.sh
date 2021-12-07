#!/bin/bash
set -eou pipefail
dir=$(dirname $0)

# Clean up coverage and stuff.
make -C test clean

# Run sharness tests.
cp -vf logging.conf logging.conf.bak
cp -vf logging.prod.conf logging.conf
bash $dir/run-sharness.sh
cp -vf logging.conf.bak logging.conf

# Run Python tests with MariaDB database.
# Pass --silence to avoid reporting coverage. We will do that below.
bash $dir/run-pytests.sh --no-coverage

make -C test coverage

# /data is mounted as a volume. Copy coverage into it.
# Users can then sanitize the coverage locally in their
# aurweb root directory: ./util/fix-coverage ./data/.coverage
rm -f /data/.coverage
cp -v .coverage /data/.coverage
chmod 666 /data/.coverage

# Run flake8 and isort checks.
for dir in aurweb test migrations; do
    flake8 --count $dir
    isort --check-only $dir
done
