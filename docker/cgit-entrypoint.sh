#!/bin/bash
set -eou pipefail

mkdir -p /var/cache/cgit

cp -vf conf/cgitrc.proto /etc/cgitrc
sed -ri "s|clone-prefix=.*|clone-prefix=${CGIT_CLONE_PREFIX}|" /etc/cgitrc
sed -ri 's|header=.*|header=/aurweb/web/template/cgit/header.html|' /etc/cgitrc
sed -ri 's|footer=.*|footer=/aurweb/web/template/cgit/footer.html|' /etc/cgitrc
sed -ri 's|repo\.path=.*|repo.path=/aurweb/aur.git|' /etc/cgitrc

exec "$@"
