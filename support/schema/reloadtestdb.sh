#!/bin/sh

mydir=`pwd`
if [ `basename $mydir` != "schema" ]; then
	echo "you must be in the aur/support/schema directory to run this script"
	exit
fi

echo "dropping old database..."
yes | mysqladmin -uaur -paur drop AUR

echo "recreating database..."
mysqladmin -uaur -paur create AUR

echo "recreating tables..."
mysql -uaur -paur AUR < ./aur-schema.sql

echo "loading dummy-data..."
bzcat ./dummy-data.sql.bz2 | mysql -uaur -paur AUR

echo "done."
exit

