#!/bin/bash

cd /aurweb
aurweb-aurblup
if [ $? -eq 0 ]; then
    echo "[$(date -u)] executed aurblup" >> /var/log/aurblup.log
fi

aurweb-mkpkglists
if [ $? -eq 0 ]; then
    echo "[$(date -u)] executed mkpkglists" >> /var/log/mkpkglists.log
fi

exec /usr/bin/crond -n
