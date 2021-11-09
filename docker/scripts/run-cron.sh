#!/bin/bash

cd /aurweb
aurweb-aurblup
aurweb-mkpkglists

exec /usr/bin/crond -n
