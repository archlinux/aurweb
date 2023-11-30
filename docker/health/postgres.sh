#!/bin/bash
exec su postgres -c 'pg_isready'
