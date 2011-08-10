#!/bin/bash

DRYRUN=${DRYRUN:-1}

source="$1"
dest="$2"

if [[ -z $source || -z $dest ]]; then
	echo 'usage: uploadbuckets.sh <source> <dest>'
	echo 'Script runs in DRYRUN mode by default.'
	echo 'To run for real, set DRYRUN=0 in your environment.'
	exit 1
fi

if [[ ! -d $source ]]; then
	echo 'error: source is not a directory'
	exit 1
fi

if [[ -e $dest && ! -d $dest ]]; then
	echo 'error: dest is not a directory'
	exit 1
fi

if [[ $(readlink -e $dest) = $(readlink -e $source) ]]; then
	echo 'error: source and dest cannot be the same. Rotate the result'
	echo 'into place once the migration is complete.'
	exit 1
fi

if [[ ! -d $dest ]]; then
	mkdir $dest
fi

shopt -s nullglob

for package in "$source"/*; do
	pkgname="${package##*/}"
	newfolder="$dest/${pkgname:0:2}"
	if [[ ! -d "$newfolder" ]]; then
		if [[ $DRYRUN -gt 0 ]]; then
			echo mkdir -p "$newfolder"
		else
			mkdir -p "$newfolder"
		fi
	fi
	if [[ $DRYRUN -gt 0 ]]; then
		echo mv "$source/$pkgname" "$newfolder/$pkgname"
	else
		mv "$source/$pkgname" "$newfolder/$pkgname"
	fi
done

if [[ $DRYRUN -gt 0 ]]; then
	echo
	echo 'DRYRUN mode was enabled.'
	echo 'To run for real, set DRYRUN=0 in your environment.'
fi
