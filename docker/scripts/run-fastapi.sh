#!/bin/bash

CERT=/cache/localhost.cert.pem
KEY=/cache/localhost.key.pem

# If production.{cert,key}.pem exists, prefer them. This allows
# user customization of the certificates that FastAPI uses.
if [ -f /cache/production.cert.pem ]; then
    CERT=/cache/production.cert.pem
fi
if [ -f /cache/production.key.pem ]; then
    KEY=/cache/production.key.pem
fi

if [ "$1" == "uvicorn" ] || [ "$1" == "" ]; then
    exec uvicorn --reload \
        --ssl-certfile "$CERT" \
        --ssl-keyfile "$KEY" \
        --log-config /docker/logging.conf \
        --host "0.0.0.0" \
        --port 8000 \
        aurweb.asgi:app
else
    exec hypercorn --reload \
        --certfile "$CERT" \
        --keyfile "$KEY" \
        --log-config /docker/logging.conf \
        -b "0.0.0.0:8000" \
        aurweb.asgi:app
fi
