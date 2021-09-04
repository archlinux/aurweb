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

DB_NAME="aurweb"
DB_HOST="mariadb"
DB_USER="aur"
DB_PASS="aur"

# Setup a config for our mysql db.
cp -vf conf/config.dev $AUR_CONFIG
sed -i "s;YOUR_AUR_ROOT;$(pwd);g" $AUR_CONFIG
sed -ri "s/^(name) = .+/\1 = ${DB_NAME}/" $AUR_CONFIG
sed -ri "s/^(host) = .+/\1 = ${DB_HOST}/" $AUR_CONFIG
sed -ri "s/^(user) = .+/\1 = ${DB_USER}/" $AUR_CONFIG
sed -ri "s/^;?(password) = .+/\1 = ${DB_PASS}/" $AUR_CONFIG

AUR_CONFIG_DEFAULTS="${AUR_CONFIG}.defaults"

if [[ "$AUR_CONFIG_DEFAULTS" != "/aurweb/conf/config.defaults" ]]; then
    cp -vf conf/config.defaults $AUR_CONFIG_DEFAULTS
fi

# Set some defaults needed for pathing and ssh uris.
sed -ri "s|^(repo-path) = .+|\1 = /aurweb/aur.git/|" $AUR_CONFIG_DEFAULTS

ssh_cmdline='ssh ssh://aur@localhost:2222'
sed -ri "s|^(ssh-cmdline) = .+|\1 = $ssh_cmdline|" $AUR_CONFIG_DEFAULTS

# Setup SSH Keys.
ssh-keygen -A

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
    ln -sf /usr/local/bin/aurweb-git-update hooks/update
    cd $curdir
    chown -R aur:aur $GIT_REPO
fi

exec "$@"
