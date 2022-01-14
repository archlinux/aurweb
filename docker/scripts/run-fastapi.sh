#!/bin/bash
# By default, set FASTAPI_WORKERS to 2. In production, this should
# be configured by the deployer.
if [ -z ${FASTAPI_WORKERS+x} ]; then
    FASTAPI_WORKERS=2
fi

export FASTAPI_BACKEND="$1"

echo "FASTAPI_BACKEND: $FASTAPI_BACKEND"
echo "FASTAPI_WORKERS: $FASTAPI_WORKERS"

# Perform migrations.
alembic upgrade head

if [ "$1" == "uvicorn" ] || [ "$1" == "" ]; then
    exec uvicorn --reload \
        --log-config /docker/logging.conf \
        --host "0.0.0.0" \
        --port 8000 \
        aurweb.asgi:app
elif [ "$1" == "gunicorn" ]; then
    exec gunicorn \
        --log-config /docker/logging.conf \
        --proxy-protocol \
        --bind "0.0.0.0:8000" \
        -w $FASTAPI_WORKERS \
        -k uvicorn.workers.UvicornWorker \
        aurweb.asgi:app
elif [ "$1" == "hypercorn" ]; then
    exec hypercorn --reload \
        --log-config /docker/logging.conf \
        -b "0.0.0.0:8000" \
        aurweb.asgi:app
else
    echo "Error: Invalid \$FASTAPI_BACKEND supplied."
    echo "Valid backends: 'uvicorn', 'gunicorn', 'hypercorn'."
    exit 1
fi
