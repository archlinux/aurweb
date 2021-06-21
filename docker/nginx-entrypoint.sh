#!/bin/bash
set -eou pipefail

# Setup a config for our mysql db.
cp -vf conf/config.dev conf/config
sed -i "s;YOUR_AUR_ROOT;$(pwd);g" conf/config
sed -ri 's/^(host) = .+/\1 = mariadb/' conf/config
sed -ri 's/^(user) = .+/\1 = aur/' conf/config
sed -ri 's/^;?(password) = .+/\1 = aur/' conf/config

# Setup http(s) stuff.
sed -ri "s|^(aur_location) = .+|\1 = https://localhost:8444|" conf/config
sed -ri 's/^(disable_http_login) = .+/\1 = 1/' conf/config

cp -vf /cache/localhost.cert.pem /etc/ssl/certs/localhost.cert.pem
cp -vf /cache/localhost.key.pem /etc/ssl/private/localhost.key.pem

cat > /etc/nginx/nginx.conf << EOF
daemon off;
user root;
worker_processes auto;
pid /var/run/nginx.pid;
include /etc/nginx/modules-enabled/*.conf;

events {
    worker_connections 256;
}

http {
    sendfile on;
    tcp_nopush on;
    types_hash_max_size 4096;
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    ssl_protocols TLSv1 TLSv1.1 TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;

    access_log /var/log/nginx/access.log;
    error_log /var/log/nginx/error.log;

    gzip on;

    upstream hypercorn {
        server fastapi:8000;
    }

    upstream cgit {
        server cgit:3000;
    }

    server {
        listen 8443 ssl http2;
        server_name localhost default_server;

        ssl_certificate /etc/ssl/certs/localhost.cert.pem;
        ssl_certificate_key /etc/ssl/private/localhost.key.pem;

        root /aurweb/web/html;
        index index.php;

        location ~ ^/cgit {
            include uwsgi_params;
            rewrite ^/cgit/([^?/]+/[^?]*)?(?:\?(.*))?$ /cgit.cgi?url=\$1&\$2 last;
            uwsgi_modifier1 9;
            uwsgi_param CGIT_CONFIG /etc/cgitrc;
            uwsgi_pass uwsgi://cgit;
        }

        location ~ ^/[^/]+\.php($|/) {
            fastcgi_pass   php-fpm:9000;
            fastcgi_index  index.php;
            fastcgi_split_path_info ^(/[^/]+\.php)(/.*)\$;
            fastcgi_param  SCRIPT_FILENAME  \$document_root\$fastcgi_script_name;
            fastcgi_param  PATH_INFO        \$fastcgi_path_info;
            include        fastcgi_params;
        }

        location ~ .* {
            rewrite ^/(.*)$ /index.php/\$1 last;
        }

    }

    server {
        listen 8444 ssl http2;
        server_name localhost default_server;

        ssl_certificate /etc/ssl/certs/localhost.cert.pem;
        ssl_certificate_key /etc/ssl/private/localhost.key.pem;

        root /aurweb/web/html;

        location / {
            try_files \$uri @proxy_to_app;
        }

        location ~ ^/cgit {
            include uwsgi_params;
            rewrite ^/cgit/([^?/]+/[^?]*)?(?:\?(.*))?$ /cgit.cgi?url=\$1&\$2 last;
            uwsgi_modifier1 9;
            uwsgi_param CGIT_CONFIG /etc/cgitrc;
            uwsgi_pass uwsgi://cgit;
        }

        location @proxy_to_app {
            proxy_set_header Host \$http_host;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
            proxy_redirect off;
            proxy_buffering off;
            proxy_pass https://hypercorn;
        }
    }

    map \$http_upgrade \$connection_upgrade {
        default upgrade;
        '' close;
    }
}
EOF

exec "$@"
