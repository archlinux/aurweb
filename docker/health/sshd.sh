#!/bin/bash
# Opt to just pgrep sshd instead of connecting here. This health
# script is used on a regular interval and it ends up spamming
# the git service's logs with accesses.
exec pgrep sshd
