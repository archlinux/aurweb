#!/bin/bash

echo "=== Running nginx server! ==="
echo
echo " Services:"
echo "  - FastAPI : https://localhost:8444/"
echo "     (cgit) : https://localhost:8444/cgit/"
echo "  - PHP     : https://localhost:8443/"
echo "     (cgit) : https://localhost:8443/cgit/"
echo
echo " Note: Copy root CA (./cache/ca.root.pem) to ca-certificates or browser."
echo
echo " Thanks for using aurweb!"
echo

exec nginx -c /etc/nginx/nginx.conf
