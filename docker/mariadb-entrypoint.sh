#!/bin/bash
set -eou pipefail

MYSQL_DATA=/var/lib/mysql

mariadb-install-db --user=mysql --basedir=/usr --datadir=$MYSQL_DATA

# Start it up.
mysqld_safe --datadir=$MYSQL_DATA --skip-networking &
while ! mysqladmin ping 2>/dev/null; do
    sleep 1s
done

# Configure databases.
DATABASE="aurweb" # Persistent database for fastapi.

echo "Taking care of primary database '${DATABASE}'..."
mysql -u root -e "CREATE USER IF NOT EXISTS 'aur'@'localhost' IDENTIFIED BY 'aur';"
mysql -u root -e "CREATE USER IF NOT EXISTS 'aur'@'%' IDENTIFIED BY 'aur';"
mysql -u root -e "CREATE DATABASE IF NOT EXISTS $DATABASE;"

mysql -u root -e "CREATE USER IF NOT EXISTS 'aur'@'%' IDENTIFIED BY 'aur';"
mysql -u root -e "GRANT ALL ON aurweb.* TO 'aur'@'localhost';"
mysql -u root -e "GRANT ALL ON aurweb.* TO 'aur'@'%';"

mysql -u root -e "CREATE USER IF NOT EXISTS 'root'@'%' IDENTIFIED BY 'aur';"
mysql -u root -e "GRANT ALL ON *.* TO 'root'@'%' WITH GRANT OPTION;"

mysqladmin -uroot shutdown

exec "$@"
