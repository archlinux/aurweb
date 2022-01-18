#!/bin/bash
exec /usr/bin/memcached -u memcached -m 64 -c 1024 -l 0.0.0.0
