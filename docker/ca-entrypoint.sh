#!/bin/bash
set -eou pipefail

if [ -f /cache/ca.root.pem ]; then
    echo "Already have certs, skipping."
    exit 0
fi

# Generate a new 2048-bit RSA key for the Root CA.
openssl genrsa -des3 -out /cache/ca.key -passout pass:devca 2048

# Request and self-sign a new Root CA certificate, using
# the RSA key. Output Root CA PEM-format certificate and key:
# /cache/ca.root.pem and /cache/ca.key.pem
openssl req -x509 -new -nodes -sha256 -days 1825 \
    -passin pass:devca \
    -subj "/C=US/ST=California/L=Authority/O=aurweb/CN=localhost" \
    -in /cache/ca.key -out /cache/ca.root.pem -keyout /cache/ca.key.pem

# Generate a new 2048-bit RSA key for a localhost server.
openssl genrsa -out /cache/localhost.key 2048

# Generate a Certificate Signing Request (CSR) for the localhost server
# using the RSA key we generated above.
openssl req -new -key /cache/localhost.key -passout pass:devca \
    -subj "/C=US/ST=California/L=Server/O=aurweb/CN=localhost" \
    -out /cache/localhost.csr

# Get our CSR signed by our Root CA PEM-formatted certificate and key
# to produce a fresh /cache/localhost.cert.pem PEM-formatted certificate.
openssl x509 -req -in /cache/localhost.csr \
    -CA /cache/ca.root.pem -CAkey /cache/ca.key.pem \
    -CAcreateserial \
    -out /cache/localhost.cert.pem \
    -days 825 -sha256 \
    -passin pass:devca \
    -extfile /docker/localhost.ext

# Convert RSA key to a PEM-formatted key: /cache/localhost.key.pem
openssl rsa -in /cache/localhost.key -text > /cache/localhost.key.pem

# At the end here, our notable certificates and keys are:
#   - /cache/ca.root.pem
#   - /cache/ca.key.pem
#   - /cache/localhost.key.pem
#   - /cache/localhost.cert.pem
#
# When running a server which uses the localhost certificate, a chain
# should be used, starting with localhost.cert.pem:
#   - cat /cache/localhost.cert.pem /cache/ca.root.pem > localhost.chain.pem
#
# The Root CA (ca.root.pem) should be imported into browsers or
# ca-certificates on machines wishing to verify localhost.
#

chmod 666 /cache/*

exec "$@"
