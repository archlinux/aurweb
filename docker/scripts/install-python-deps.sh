#!/bin/bash
set -eou pipefail

if [ ! -z "${COMPOSE+x}" ]; then
    export PIP_BREAK_SYSTEM_PACKAGES=1
    poetry config virtualenvs.create false
fi
poetry install --no-interaction --no-ansi
