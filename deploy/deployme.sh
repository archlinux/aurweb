#!/usr/bin/env bash

set -eux

BASEDIR=$(dirname $(readlink -f "$0"))
cd "$BASEDIR/.."
echo "=> Deploying in $(pwd)"
git fetch origin && git reset --hard origin/master
( cd doc/ && make )
( cd po/ && make && make install )
alembic upgrade head
