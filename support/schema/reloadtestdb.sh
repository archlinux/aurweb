#!/bin/sh

mydir=`pwd`
if [ `basename $mydir` != "schema" ]; then
	echo "you must be in the aur/support/schema directory to run this script"
	exit
fi

echo "recreating database..."
mysql -uaur -paur AUR < ./aur-schema.sql

echo "loading dummy-data..."
bzcat ./dummy-data.sql.bz2 | mysql -uaur -paur AUR

echo "done."
exit

