#!/bin/bash
set -eou pipefail

# Upgrade PIP; Arch Linux's version of pip is outdated for Poetry.
pip install --upgrade pip

# Install the aurweb package and deps system-wide via poetry.
poetry config virtualenvs.create false
poetry update
poetry build
poetry install --no-interaction --no-ansi

exec "$@"
