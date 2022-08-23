#!/bin/bash
set -eou pipefail

# Upgrade PIP; Arch Linux's version of pip is outdated for Poetry.
pip install --upgrade pip

if [ ! -z "${COMPOSE+x}" ]; then
    poetry config virtualenvs.create false
fi
poetry install --no-interaction --no-ansi
