#!/bin/bash

mysqld_safe --datadir=/var/lib/mysql --skip-networking &
until mysqladmin ping --silent; do
    sleep 1s
done

# Create test database.
mysql -u root -e "CREATE USER 'aur'@'%' IDENTIFIED BY 'aur'" \
    2>/dev/null || /bin/true
mysql -u root -e "DROP DATABASE aurweb_test" 2>/dev/null || /bin/true
mysql -u root -e "CREATE DATABASE aurweb_test"
mysql -u root -e "GRANT ALL PRIVILEGES ON aurweb_test.* TO 'aur'@'%'"
mysql -u root -e "FLUSH PRIVILEGES"

# Shutdown mariadb.
mysqladmin -uroot shutdown

exec "$@"
