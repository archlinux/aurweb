#!/bin/bash -e

DB_NAME=${DB_NAME:-AUR}
DB_USER=${DB_USER:-aur}
# Password should allow empty definition
DB_PASS=${DB_PASS-aur}
DB_HOST=${DB_HOST:-localhost}
DATA_FILE=${DATA_FILE:-dummy-data.sql}

echo "Using database $DB_NAME, user $DB_USER, host $DB_HOST"

mydir=$(pwd)
if [ $(basename $mydir) != "schema" ]; then
	echo "you must be in the aur/support/schema directory to run this script"
	exit 1
fi

echo "recreating database..."
mysql -h $DB_HOST -u $DB_USER -p$DB_PASS < aur-schema.sql

if [ ! -f $DATA_FILE ]; then
	echo "creating dumy-data..."
	python3 gendummydata.py $DATA_FILE
fi

echo "loading dummy-data..."
mysql -h $DB_HOST -u $DB_USER -p$DB_PASS $DB_NAME < $DATA_FILE

echo "done."
