#!/bin/bash
set -eou pipefail

# Prepare AUR_CONFIG.
cp -vf conf/config.dev conf/config
sed -i "s;YOUR_AUR_ROOT;$(pwd);g" conf/config

# Create directories we need.
mkdir -p /aurweb/aurblup

# Install the cron configuration.
cp /docker/config/aurweb-cron /etc/cron.d/aurweb-cron
chmod 0644 /etc/cron.d/aurweb-cron
crontab /etc/cron.d/aurweb-cron

exec "$@"
