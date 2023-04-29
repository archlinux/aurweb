#!/bin/bash
set -eou pipefail

mkdir -p /var/data/cgit

cp -vf conf/cgitrc.proto /etc/cgitrc
sed -ri "s|clone-prefix=.*|clone-prefix=${CGIT_CLONE_PREFIX}|" /etc/cgitrc
sed -ri 's|header=.*|header=/aurweb/static/html/cgit/header.html|' /etc/cgitrc
sed -ri 's|footer=.*|footer=/aurweb/static/html/cgit/footer.html|' /etc/cgitrc
sed -ri 's|repo\.path=.*|repo.path=/aurweb/aur.git|' /etc/cgitrc
sed -ri "s|^(css)=.*$|\1=${CGIT_CSS}|" /etc/cgitrc

exec "$@"
