#!/bin/bash
# Initialize step-ca and request certificates from it.
#
# Certificates created by this service are meant to be used in
# aurweb Docker's nginx service.
#
# If ./data/root_ca.crt is present, CA generation is skipped.
# If ./data/${host}.{cert,key}.pem is available, host certificate
# generation is skipped.
#
set -eou pipefail

# /data-based variables.
DATA_DIR="/data"
DATA_ROOT_CA="$DATA_DIR/root_ca.crt"
DATA_CERT="$DATA_DIR/localhost.cert.pem"
DATA_CERT_KEY="$DATA_DIR/localhost.key.pem"

# Host certificates requested from the CA (separated by spaces).
DATA_CERT_HOSTS='localhost'

# Local step paths and CA configuration values.
STEP_DIR="$(step-cli path)"
STEP_CA_CONFIG="$STEP_DIR/config/ca.json"
STEP_CA_ADDR='127.0.0.1:8443'
STEP_CA_URL='https://localhost:8443'
STEP_CA_PROVISIONER='admin@localhost'

# Password file used for both --password-file and --provisioner-password-file.
STEP_PASSWD_FILE="$STEP_DIR/password.txt"

# Hostnames supported by the CA.
STEP_CA_NAME='aurweb'
STEP_CA_DNS='localhost'

make_password() {
    # Create a random 20-length password and write it to $1.
    openssl rand -hex 20 > $1
}

setup_step_ca() {
    # Cleanup and setup step ca configuration.
    rm -rf $STEP_DIR/*

    # Initialize `step`
    make_password "$STEP_PASSWD_FILE"
    step-cli ca init \
        --name="$STEP_CA_NAME" \
        --dns="$STEP_CA_DNS" \
        --address="$STEP_CA_ADDR" \
        --password-file="$STEP_PASSWD_FILE" \
        --provisioner="$STEP_CA_PROVISIONER" \
        --provisioner-password-file="$STEP_PASSWD_FILE" \
        --with-ca-url="$STEP_CA_URL"

    # Update ca.json max TLS certificate duration to a year.
    update-step-config "$STEP_CA_CONFIG"

    # Install root_ca.crt as read/writable to /data/root_ca.crt.
    install -m666 "$STEP_DIR/certs/root_ca.crt" "$DATA_ROOT_CA"
}

start_step_ca() {
    # Start the step-ca web server.
    step-ca "$STEP_CA_CONFIG" \
        --password-file="$STEP_PASSWD_FILE" &
    until printf "" 2>>/dev/null >>/dev/tcp/127.0.0.1/8443; do
       sleep 1
    done
}

kill_step_ca() {
    # Stop the step-ca web server.
    killall step-ca >/dev/null 2>&1 || /bin/true
}

install_step_ca() {
    # Install step-ca certificate authority to the system.
    step-cli certificate install "$STEP_DIR/certs/root_ca.crt"
}

step_cert_request() {
    # Request a certificate from the step ca.
    step-cli ca certificate \
        --not-after=8800h \
        --provisioner="$STEP_CA_PROVISIONER" \
        --provisioner-password-file="$STEP_PASSWD_FILE" \
        $1 $2 $3
    chmod 666 /data/${1}.*.pem
}

if [ ! -f $DATA_ROOT_CA ]; then
    setup_step_ca
    install_step_ca
fi

# For all hosts separated by spaces in $DATA_CERT_HOSTS, perform a check
# for their existence in /data and react accordingly.
for host in $DATA_CERT_HOSTS; do
    if [ -f /data/${host}.cert.pem ] && [ -f /data/${host}.key.pem ]; then
        # Found an override. Move on to running the service after
        # printing a notification to the user.
        echo "Found '${host}.{cert,key}.pem' override, skipping..."
        echo -n "Note: If you need to regenerate certificates, run "
        echo '`rm -f data/*.{cert,key}.pem` before starting this service.'
        exec "$@"
    else
        # Otherwise, we had a missing cert or key, so remove both.
        rm -f /data/${host}.cert.pem
        rm -f /data/${host}.key.pem
    fi
done

start_step_ca
for host in $DATA_CERT_HOSTS; do
    step_cert_request $host /data/${host}.cert.pem /data/${host}.key.pem
done
kill_step_ca

# Set permissions to /data to rwx for everybody.
chmod 777 /data

exec "$@"
