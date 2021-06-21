#!/bin/bash
set -eou pipefail

SSHD_CONFIG=/etc/ssh/sshd_config

GIT_REPO=aur.git
GIT_KEY=/cache/git.key

# Setup SSH Keys.
ssh-keygen -A

# Add AUR SSH config.
cat >> $SSHD_CONFIG << EOF
Match User aur
    PasswordAuthentication no
    AuthorizedKeysCommand /usr/local/bin/aurweb-git-auth "%t" "%k"
    AuthorizedKeysCommandUser aur
    AcceptEnv AUR_OVERWRITE
    SetEnv AUR_CONFIG=/aurweb/config/config
EOF

# Taken from INSTALL.
mkdir -pv $GIT_REPO

# Initialize git repository.
if [ ! -f $GIT_REPO/config ]; then
    cd $GIT_REPO
    git init --bare
    git config --local transfer.hideRefs '^refs/'
    git config --local --add transfer.hideRefs '!refs/'
    git config --local --add transfer.hideRefs '!HEAD'
    ln -sf /usr/local/bin/aurweb-git-update hooks/update
    chown -R aur .
    cd ..
fi

if [ ! -f $GIT_KEY ]; then
    # Create a DSA ssh private/pubkey at /cache/git.key{.pub,}.
    ssh-keygen -f $GIT_KEY -t dsa -N '' -C 'AUR Git Key'
fi

# Users should modify these permissions on their local machines.
chmod 666 ${GIT_KEY}{.pub,}

exec "$@"
