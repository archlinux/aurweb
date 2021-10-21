#!/bin/bash
exec uwsgi --socket 0.0.0.0:${1} \
    --plugins cgi \
    --cgi /usr/share/webapps/cgit-aurweb/cgit.cgi
