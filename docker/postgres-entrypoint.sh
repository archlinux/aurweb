#!/bin/bash
set -eou pipefail

PGDATA=/var/lib/postgres/data
DATABASE="aurweb"

# Initialize and setup postgres
if [ ! -f "$PGDATA/../init" ]; then
    echo "Preparing postgres instance..."
    touch $PGDATA/../init

    # Init db directory
    su postgres -c "pg_ctl initdb -D $PGDATA"
    su postgres -c "echo \"listen_addresses='*'\" >> $PGDATA/postgresql.conf"
    su postgres -c "echo \"host all all 0.0.0.0/0 scram-sha-256\" >> $PGDATA/pg_hba.conf"
    install -d -o postgres -g postgres /run/postgresql

    # Start postgres
    su postgres -c "pg_ctl start -D $PGDATA"

    # Configure database & user
    echo "Taking care of primary database '$DATABASE'..."
    su postgres -c "psql -c \"create database $DATABASE;\""
    su postgres -c "psql -c \"create role aur superuser login password 'aur';\"";

    # Provision database
    python -m aurweb.initdb 2>/dev/null || /bin/true

    # Stop postgres
    su postgres -c "pg_ctl stop -D $PGDATA"

fi

exec "$@"
