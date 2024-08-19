#!/bin/bash
set -eou pipefail

MYSQL_DATA=/var/lib/mysql

mariadb-install-db --user=mysql --basedir=/usr --datadir=$MYSQL_DATA

# Start it up.
mariadbd-safe --datadir=$MYSQL_DATA --skip-networking &
while ! mariadb-admin ping 2>/dev/null; do
    sleep 1s
done

# Configure databases.
DATABASE="aurweb" # Persistent database for fastapi.

echo "Taking care of primary database '${DATABASE}'..."
mariadb -u root -e "CREATE USER IF NOT EXISTS 'aur'@'localhost' IDENTIFIED BY 'aur';"
mariadb -u root -e "CREATE USER IF NOT EXISTS 'aur'@'%' IDENTIFIED BY 'aur';"
mariadb -u root -e "CREATE DATABASE IF NOT EXISTS $DATABASE;"

mariadb -u root -e "CREATE USER IF NOT EXISTS 'aur'@'%' IDENTIFIED BY 'aur';"
mariadb -u root -e "GRANT ALL ON aurweb.* TO 'aur'@'localhost';"
mariadb -u root -e "GRANT ALL ON aurweb.* TO 'aur'@'%';"

mariadb -u root -e "CREATE USER IF NOT EXISTS 'root'@'%' IDENTIFIED BY 'aur';"
mariadb -u root -e "GRANT ALL ON *.* TO 'root'@'%' WITH GRANT OPTION;"

mariadb-admin -uroot shutdown

exec "$@"
