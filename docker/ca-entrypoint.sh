#!/bin/bash
set -eou pipefail

if [ -f /cache/localhost.cert.pem ] && \
    [ -f /cache/localhost.key.pem ] && \
    [ -f /cache/ca.root.pem ]; then
    echo "Already have certs, skipping."
    exec "$@"
fi

openssl genrsa -des3 -out ca.key \
    -passout pass:devca 2048

openssl req -x509 -new -nodes \
    -key ca.key -sha256 -days 1825 \
    -out /cache/ca.root.pem \
    -subj "/C=US/ST=California/L=Nowhere/O=aurweb/CN=localhost" \
    --passin pass:devca

# Generate keys for aurweb.
openssl req -nodes -newkey rsa:2048 -keyout /cache/localhost.key.pem \
    -out localhost.csr \
    -subj "/C=US/ST=California/L=Nowhere/O=aurweb/CN=localhost"

echo "$(hexdump -n 16 -e '4/4 "%08X" 1 "\n"' /dev/random)" \
    > /cache/ca.root.srl
openssl x509 -req -in localhost.csr -CA /cache/ca.root.pem \
    -CAkey ca.key -CAserial /cache/ca.root.srl \
    -out /cache/localhost.cert.pem \
    -days 825 -sha256 -extfile /docker/ca.ext \
    --passin pass:devca

chmod 666 /cache/localhost.{key,cert}.pem
chmod 666 /cache/ca.root.pem

exec "$@"
