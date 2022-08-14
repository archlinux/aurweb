#!/bin/bash

# Update this every time.
chown -R aur:aur /aurweb/aur.git

# Start up sshd
exec /usr/sbin/sshd -e -p 2222 -D
