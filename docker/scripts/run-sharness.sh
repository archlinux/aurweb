#!/bin/bash
set -eou pipefail

# Initialize the new database; ignore errors.
python -m aurweb.initdb 2>/dev/null || /bin/true

eatmydata -- make -C test sh
