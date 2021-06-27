#!/bin/bash

exec uwsgi \
    --socket /var/run/smartgit/smartgit.sock \
    --uid root \
    --gid http \
    --chmod-socket=666 \
    --plugins cgi \
    --cgi /usr/lib/git-core/git-http-backend
