#!/bin/bash

# Initialize the new database; ignore errors.
python -m aurweb.initdb 2>/dev/null || /bin/true

exec hypercorn --reload \
    --certfile /cache/localhost.cert.pem \
    --keyfile /cache/localhost.key.pem \
    --error-logfile - \
    --log-config docker/logging.conf \
    -b "0.0.0.0:8000" aurweb.asgi:app
