#!/bin/bash
set -eou pipefail

SSHD_CONFIG=/etc/ssh/sshd_config
AUTH_SCRIPT=/app/git-auth.sh

GIT_REPO=/aurweb/aur.git
GIT_BRANCH=master # 'Master' branch.

if ! grep -q 'PYTHONPATH' /etc/environment; then
    echo "PYTHONPATH='/aurweb:/aurweb/app'" >> /etc/environment
else
    sed -ri "s|^(PYTHONPATH)=.*$|\1='/aurweb'|" /etc/environment
fi

if ! grep -q 'AUR_CONFIG' /etc/environment; then
    echo "AUR_CONFIG='/aurweb/conf/config'" >> /etc/environment
else
    sed -ri "s|^(AUR_CONFIG)=.*$|\1='/aurweb/conf/config'|" /etc/environment
fi

mkdir -p /app
chmod 755 /app

cat >> $AUTH_SCRIPT << EOF
#!/usr/bin/env bash
export AUR_CONFIG="$AUR_CONFIG"
exec /usr/bin/aurweb-git-auth "\$@"
EOF
chmod 755 $AUTH_SCRIPT

# Add AUR SSH config.
cat >> $SSHD_CONFIG << EOF
Match User aur
    PasswordAuthentication no
    AuthorizedKeysCommand $AUTH_SCRIPT "%t" "%k"
    AuthorizedKeysCommandUser aur
    AcceptEnv AUR_OVERWRITE
EOF

# Setup database.
NO_INITDB=1 /docker/mariadb-init-entrypoint.sh

# Setup some other options.
aurweb-config set serve repo-path '/aurweb/aur.git/'
aurweb-config set serve ssh-cmdline "$SSH_CMDLINE"

# Setup SSH Keys.
ssh-keygen -A

# In docker-compose.aur-dev.yml, we bind ./data to /aurweb/data.
# Production users wishing to include their own SSH keys should
# supply them in ./data.
if [ -d /aurweb/data ]; then
    find /aurweb/data -type f -name 'ssh_host_*' -exec cp -vf "{}" /etc/ssh/ \;
fi

# Taken from INSTALL.
mkdir -pv $GIT_REPO

# Initialize git repository.
if [ ! -f $GIT_REPO/config ]; then
    curdir="$(pwd)"
    cd $GIT_REPO
    git config --global init.defaultBranch $GIT_BRANCH
    git init --bare
    git config --local transfer.hideRefs '^refs/'
    git config --local --add transfer.hideRefs '!refs/'
    git config --local --add transfer.hideRefs '!HEAD'
    ln -sf /usr/bin/aurweb-git-update hooks/update
    cd $curdir
    chown -R aur:aur $GIT_REPO
fi

exec "$@"
