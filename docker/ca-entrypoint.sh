#!/bin/bash
set -eou pipefail

if [ -f /data/ca.root.pem ]; then
    echo "Already have certs, skipping."
    exit 0
fi

# Generate a new 2048-bit RSA key for the Root CA.
openssl genrsa -des3 -out /data/ca.key -passout pass:devca 2048

# Request and self-sign a new Root CA certificate, using
# the RSA key. Output Root CA PEM-format certificate and key:
# /data/ca.root.pem and /data/ca.key.pem
openssl req -x509 -new -nodes -sha256 -days 1825 \
    -passin pass:devca \
    -subj "/C=US/ST=California/L=Authority/O=aurweb/CN=localhost" \
    -in /data/ca.key -out /data/ca.root.pem -keyout /data/ca.key.pem

# Generate a new 2048-bit RSA key for a localhost server.
openssl genrsa -out /data/localhost.key 2048

# Generate a Certificate Signing Request (CSR) for the localhost server
# using the RSA key we generated above.
openssl req -new -key /data/localhost.key -passout pass:devca \
    -subj "/C=US/ST=California/L=Server/O=aurweb/CN=localhost" \
    -out /data/localhost.csr

# Get our CSR signed by our Root CA PEM-formatted certificate and key
# to produce a fresh /data/localhost.cert.pem PEM-formatted certificate.
openssl x509 -req -in /data/localhost.csr \
    -CA /data/ca.root.pem -CAkey /data/ca.key.pem \
    -CAcreateserial \
    -out /data/localhost.cert.pem \
    -days 825 -sha256 \
    -passin pass:devca \
    -extfile /docker/localhost.ext

# Convert RSA key to a PEM-formatted key: /data/localhost.key.pem
openssl rsa -in /data/localhost.key -text > /data/localhost.key.pem

# At the end here, our notable certificates and keys are:
#   - /data/ca.root.pem
#   - /data/ca.key.pem
#   - /data/localhost.key.pem
#   - /data/localhost.cert.pem
#
# When running a server which uses the localhost certificate, a chain
# should be used, starting with localhost.cert.pem:
#   - cat /data/localhost.cert.pem /data/ca.root.pem > localhost.chain.pem
#
# The Root CA (ca.root.pem) should be imported into browsers or
# ca-certificates on machines wishing to verify localhost.
#

chmod 666 /data/*

exec "$@"
