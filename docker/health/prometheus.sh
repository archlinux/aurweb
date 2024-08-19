#!/bin/sh
exec wget -q http://prometheus:9090/status -O /dev/null
