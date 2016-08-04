#!/bin/sh

test_description='git-update tests'

. ./setup.sh

test_expect_success 'Test update hook.' '
	old=0000000000000000000000000000000000000000 &&
	new=$(git -C aur.git rev-parse HEAD) &&
	SSH_ORIGINAL_COMMAND="setup-repo foobar" AUR_USER=user "$GIT_SERVE" &&
	AUR_USER=user AUR_PKGBASE=foobar AUR_PRIVILEGED=0 \
	"$GIT_UPDATE" refs/heads/master "$old" "$new" 2>&1 &&
	cat >expected <<-EOF &&
	1|1|foobar|1-1|aurweb test package.|https://aur.archlinux.org/
	EOF
	echo "SELECT * FROM Packages;" | sqlite3 aur.db >actual &&
	test_cmp expected actual
'

test_done
