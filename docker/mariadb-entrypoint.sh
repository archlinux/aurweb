#!/bin/bash
set -eou pipefail

MYSQL_DATA=/var/lib/mysql
DB_HOST="localhost"

mariadb-install-db --user=mysql --basedir=/usr --datadir=$MYSQL_DATA

# Start it up.
mysqld_safe --datadir=$MYSQL_DATA --skip-networking &
while ! mysqladmin ping 2>/dev/null; do
    sleep 1s
done

# Configure databases.
DATABASE="aurweb" # Persistent database for fastapi/php-fpm.
TEST_DB="aurweb_test" # Test database (ephemereal).

echo "Taking care of primary database '${DATABASE}'..."
mysql -u root -e "CREATE USER IF NOT EXISTS 'aur'@'$DB_HOST' IDENTIFIED BY 'aur';"
mysql -u root -e "CREATE DATABASE IF NOT EXISTS $DATABASE;"
mysql -u root -e "GRANT ALL ON ${DATABASE}.* TO 'aur'@'$DB_HOST';"

# Drop and create our test database.
echo "Dropping test database '$TEST_DB'..."
mysql -u root -e "DROP DATABASE IF EXISTS $TEST_DB;"
mysql -u root -e "CREATE DATABASE $TEST_DB;"
mysql -u root -e "GRANT ALL ON ${TEST_DB}.* TO 'aur'@'$DB_HOST';"
echo "Created new '$TEST_DB'!"

mysqladmin -uroot shutdown

exec "$@"
