#!/bin/bash
set -eou pipefail

cp -vf logging.prod.conf logging.conf

exec "$@"
