#!/bin/bash

if [ "$1" == "uvicorn" ] || [ "$1" == "" ]; then
    exec uvicorn --reload \
        --ssl-certfile /cache/localhost.cert.pem \
        --ssl-keyfile /cache/localhost.key.pem \
        --log-config /docker/logging.conf \
        --host "0.0.0.0" \
        --port 8000 \
        aurweb.asgi:app
else
    exec hypercorn --reload \
        --certfile /cache/localhost.cert.pem \
        --keyfile /cache/localhost.key.pem \
        --log-config /docker/logging.conf \
        -b "0.0.0.0:8000" \
        aurweb.asgi:app
fi
