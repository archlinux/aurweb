#!/bin/bash
STEP_DIR="$(step-cli path)"
STEP_PASSWD_FILE="$STEP_DIR/password.txt"
STEP_CA_CONFIG="$STEP_DIR/config/ca.json"

# Start the step-ca https server.
exec step-ca "$STEP_CA_CONFIG" --password-file="$STEP_PASSWD_FILE"
