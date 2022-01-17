#!/bin/bash
# Wrapper script used to call aurweb-git-update externally when
# utilizing an app-based virtualenv.
aurweb_dir="$HOME"
cd $aurweb_dir
exec poetry run aurweb-git-update "$@"
