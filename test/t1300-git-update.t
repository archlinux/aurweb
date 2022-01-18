#!/bin/sh

test_description='git-update tests'

. "$(dirname "$0")/setup.sh"

dump_package_info() {
	for t in Packages Licenses PackageLicenses Groups PackageGroups \
		PackageDepends PackageRelations PackageSources \
		PackageNotifications; do
		echo "SELECT * FROM $t;" | sqlite3 aur.db
	done
}

test_expect_success 'Test update hook on a fresh repository.' '
	old=0000000000000000000000000000000000000000 &&
	new=$(git -C aur.git rev-parse HEAD^) &&
	AUR_USER=user AUR_PKGBASE=foobar AUR_PRIVILEGED=0 \
	cover "$GIT_UPDATE" refs/heads/master "$old" "$new" 2>&1 &&
	cat >expected <<-EOF &&
	1|1|foobar|1-1|aurweb test package.|https://aur.archlinux.org/
	1|GPL
	1|1
	1|1|python-pygit2|||
	1|1
	EOF
	dump_package_info >actual &&
	test_cmp expected actual
'

test_expect_success 'Test update hook on another fresh repository.' '
	old=0000000000000000000000000000000000000000 &&
	test_when_finished "git -C aur.git checkout refs/namespaces/foobar/refs/heads/master" &&
	git -C aur.git checkout -q refs/namespaces/foobar2/refs/heads/master &&
	new=$(git -C aur.git rev-parse HEAD) &&
	AUR_USER=user AUR_PKGBASE=foobar2 AUR_PRIVILEGED=0 \
	cover "$GIT_UPDATE" refs/heads/master "$old" "$new" 2>&1 &&
	cat >expected <<-EOF &&
	1|1|foobar|1-1|aurweb test package.|https://aur.archlinux.org/
	2|2|foobar2|1-1|aurweb test package.|https://aur.archlinux.org/
	1|GPL
	2|MIT
	1|1
	2|2
	1|1|python-pygit2|||
	2|1|python-pygit2|||
	1|1
	2|1
	EOF
	dump_package_info >actual &&
	test_cmp expected actual
'

test_expect_success 'Test update hook on an updated repository.' '
	old=$(git -C aur.git rev-parse HEAD^) &&
	new=$(git -C aur.git rev-parse HEAD) &&
	AUR_USER=user AUR_PKGBASE=foobar AUR_PRIVILEGED=0 \
	cover "$GIT_UPDATE" refs/heads/master "$old" "$new" 2>&1 &&
	cat >expected <<-EOF &&
	2|2|foobar2|1-1|aurweb test package.|https://aur.archlinux.org/
	3|1|foobar|1-2|aurweb test package.|https://aur.archlinux.org/
	1|GPL
	2|MIT
	2|2
	3|1
	2|1|python-pygit2|||
	3|1|python-pygit2|||
	1|1
	2|1
	EOF
	dump_package_info >actual &&
	test_cmp expected actual
'

test_expect_success 'Test restore mode.' '
	AUR_USER=user AUR_PKGBASE=foobar AUR_PRIVILEGED=0 \
	cover "$GIT_UPDATE" restore 2>&1 &&
	cat >expected <<-EOF &&
	2|2|foobar2|1-1|aurweb test package.|https://aur.archlinux.org/
	3|1|foobar|1-2|aurweb test package.|https://aur.archlinux.org/
	1|GPL
	2|MIT
	2|2
	3|1
	2|1|python-pygit2|||
	3|1|python-pygit2|||
	1|1
	2|1
	EOF
	dump_package_info >actual &&
	test_cmp expected actual
'

test_expect_success 'Test restore mode on a non-existent repository.' '
	cat >expected <<-EOD &&
	error: restore: repository not found: foobar3
	EOD
	test_must_fail \
	env AUR_USER=user AUR_PKGBASE=foobar3 AUR_PRIVILEGED=0 \
	cover "$GIT_UPDATE" restore >actual 2>&1 &&
	test_cmp expected actual
'

test_expect_success 'Pushing to a branch other than master.' '
	old=0000000000000000000000000000000000000000 &&
	new=$(git -C aur.git rev-parse HEAD) &&
	cat >expected <<-EOD &&
	error: pushing to a branch other than master is restricted
	EOD
	test_must_fail \
	env AUR_USER=user AUR_PKGBASE=foobar AUR_PRIVILEGED=0 \
	cover "$GIT_UPDATE" refs/heads/pu "$old" "$new" >actual 2>&1 &&
	test_cmp expected actual
'

test_expect_success 'Performing a non-fast-forward ref update.' '
	old=$(git -C aur.git rev-parse HEAD) &&
	new=$(git -C aur.git rev-parse HEAD^) &&
	cat >expected <<-EOD &&
	error: denying non-fast-forward (you should pull first)
	EOD
	test_must_fail \
	env AUR_USER=user AUR_PKGBASE=foobar AUR_PRIVILEGED=0 \
	cover "$GIT_UPDATE" refs/heads/master "$old" "$new" >actual 2>&1 &&
	test_cmp expected actual
'

test_expect_success 'Performing a non-fast-forward ref update as Trusted User.' '
	old=$(git -C aur.git rev-parse HEAD) &&
	new=$(git -C aur.git rev-parse HEAD^) &&
	cat >expected <<-EOD &&
	error: denying non-fast-forward (you should pull first)
	EOD
	test_must_fail \
	env AUR_USER=tu AUR_PKGBASE=foobar AUR_PRIVILEGED=1 \
	cover "$GIT_UPDATE" refs/heads/master "$old" "$new" 2>&1 &&
	test_cmp expected actual
'

test_expect_success 'Performing a non-fast-forward ref update as normal user with AUR_OVERWRITE=1.' '
	old=$(git -C aur.git rev-parse HEAD) &&
	new=$(git -C aur.git rev-parse HEAD^) &&
	cat >expected <<-EOD &&
	error: denying non-fast-forward (you should pull first)
	EOD
	test_must_fail \
	env AUR_USER=user AUR_PKGBASE=foobar AUR_PRIVILEGED=0 AUR_OVERWRITE=1 \
	cover "$GIT_UPDATE" refs/heads/master "$old" "$new" 2>&1 &&
	test_cmp expected actual
'

test_expect_success 'Performing a non-fast-forward ref update as Trusted User with AUR_OVERWRITE=1.' '
	old=$(git -C aur.git rev-parse HEAD) &&
	new=$(git -C aur.git rev-parse HEAD^) &&
	AUR_USER=tu AUR_PKGBASE=foobar AUR_PRIVILEGED=1 AUR_OVERWRITE=1 \
	cover "$GIT_UPDATE" refs/heads/master "$old" "$new" 2>&1
'

test_expect_success 'Removing .SRCINFO.' '
	old=$(git -C aur.git rev-parse HEAD) &&
	test_when_finished "git -C aur.git reset --hard $old" &&
	git -C aur.git rm -q .SRCINFO &&
	git -C aur.git commit -q -m "Remove .SRCINFO" &&
	new=$(git -C aur.git rev-parse HEAD) &&
	test_must_fail \
	env AUR_USER=user AUR_PKGBASE=foobar AUR_PRIVILEGED=0 \
	cover "$GIT_UPDATE" refs/heads/master "$old" "$new" >actual 2>&1 &&
	grep -q "^error: missing .SRCINFO$" actual
'

test_expect_success 'Removing .SRCINFO with a follow-up fix.' '
	old=$(git -C aur.git rev-parse HEAD) &&
	test_when_finished "git -C aur.git reset --hard $old" &&
	git -C aur.git rm -q .SRCINFO &&
	git -C aur.git commit -q -m "Remove .SRCINFO" &&
	git -C aur.git revert --no-edit HEAD &&
	new=$(git -C aur.git rev-parse HEAD) &&
	test_must_fail \
	env AUR_USER=user AUR_PKGBASE=foobar AUR_PRIVILEGED=0 \
	cover "$GIT_UPDATE" refs/heads/master "$old" "$new" >actual 2>&1 &&
	grep -q "^error: missing .SRCINFO$" actual
'

test_expect_success 'Removing PKGBUILD.' '
	old=$(git -C aur.git rev-parse HEAD) &&
	test_when_finished "git -C aur.git reset --hard $old" &&
	git -C aur.git rm -q PKGBUILD &&
	git -C aur.git commit -q -m "Remove PKGBUILD" &&
	new=$(git -C aur.git rev-parse HEAD) &&
	test_must_fail \
	env AUR_USER=user AUR_PKGBASE=foobar AUR_PRIVILEGED=0 \
	cover "$GIT_UPDATE" refs/heads/master "$old" "$new" >actual 2>&1 &&
	grep -q "^error: missing PKGBUILD$" actual
'

test_expect_success 'Pushing a tree with a subdirectory.' '
	old=$(git -C aur.git rev-parse HEAD) &&
	test_when_finished "git -C aur.git reset --hard $old" &&
	mkdir aur.git/subdir &&
	touch aur.git/subdir/file &&
	git -C aur.git add subdir/file &&
	git -C aur.git commit -q -m "Add subdirectory" &&
	new=$(git -C aur.git rev-parse HEAD) &&
	test_must_fail \
	env AUR_USER=user AUR_PKGBASE=foobar AUR_PRIVILEGED=0 \
	cover "$GIT_UPDATE" refs/heads/master "$old" "$new" >actual 2>&1 &&
	grep -q "^error: the repository must not contain subdirectories$" actual
'

test_expect_success 'Pushing a tree with a large blob.' '
	old=$(git -C aur.git rev-parse HEAD) &&
	test_when_finished "git -C aur.git reset --hard $old" &&
	printf "%256001s" x >aur.git/file &&
	git -C aur.git add file &&
	git -C aur.git commit -q -m "Add large blob" &&
	new=$(git -C aur.git rev-parse HEAD) &&
	test_must_fail \
	env AUR_USER=user AUR_PKGBASE=foobar AUR_PRIVILEGED=0 \
	cover "$GIT_UPDATE" refs/heads/master "$old" "$new" >actual 2>&1 &&
	grep -q "^error: maximum blob size (250.00KiB) exceeded$" actual
'

test_expect_success 'Pushing .SRCINFO with a non-matching package base.' '
	old=$(git -C aur.git rev-parse HEAD) &&
	test_when_finished "git -C aur.git reset --hard $old" &&
	(
		cd aur.git &&
		sed "s/\(pkgbase.*\)foobar/\1foobar2/" .SRCINFO >.SRCINFO.new
		mv .SRCINFO.new .SRCINFO
		git commit -q -am "Change package base"
	) &&
	new=$(git -C aur.git rev-parse HEAD) &&
	test_must_fail \
	env AUR_USER=user AUR_PKGBASE=foobar AUR_PRIVILEGED=0 \
	cover "$GIT_UPDATE" refs/heads/master "$old" "$new" >actual 2>&1 &&
	grep -q "^error: invalid pkgbase: foobar2, expected foobar$" actual
'

test_expect_success 'Pushing .SRCINFO with invalid syntax.' '
	old=$(git -C aur.git rev-parse HEAD) &&
	test_when_finished "git -C aur.git reset --hard $old" &&
	(
		cd aur.git &&
		sed "s/=//" .SRCINFO >.SRCINFO.new
		mv .SRCINFO.new .SRCINFO
		git commit -q -am "Break .SRCINFO"
	) &&
	new=$(git -C aur.git rev-parse HEAD) &&
	test_must_fail \
	env AUR_USER=user AUR_PKGBASE=foobar AUR_PRIVILEGED=0 \
	cover "$GIT_UPDATE" refs/heads/master "$old" "$new" 2>&1
'

test_expect_success 'Pushing .SRCINFO without pkgver.' '
	old=$(git -C aur.git rev-parse HEAD) &&
	test_when_finished "git -C aur.git reset --hard $old" &&
	(
		cd aur.git &&
		sed "/pkgver/d" .SRCINFO >.SRCINFO.new
		mv .SRCINFO.new .SRCINFO
		git commit -q -am "Remove pkgver"
	) &&
	new=$(git -C aur.git rev-parse HEAD) &&
	test_must_fail \
	env AUR_USER=user AUR_PKGBASE=foobar AUR_PRIVILEGED=0 \
	cover "$GIT_UPDATE" refs/heads/master "$old" "$new" >actual 2>&1 &&
	grep -q "^error: missing mandatory field: pkgver$" actual
'

test_expect_success 'Pushing .SRCINFO without pkgrel.' '
	old=$(git -C aur.git rev-parse HEAD) &&
	test_when_finished "git -C aur.git reset --hard $old" &&
	(
		cd aur.git &&
		sed "/pkgrel/d" .SRCINFO >.SRCINFO.new
		mv .SRCINFO.new .SRCINFO
		git commit -q -am "Remove pkgrel"
	) &&
	new=$(git -C aur.git rev-parse HEAD) &&
	test_must_fail \
	env AUR_USER=user AUR_PKGBASE=foobar AUR_PRIVILEGED=0 \
	cover "$GIT_UPDATE" refs/heads/master "$old" "$new" >actual 2>&1 &&
	grep -q "^error: missing mandatory field: pkgrel$" actual
'

test_expect_success 'Pushing .SRCINFO with epoch.' '
	old=$(git -C aur.git rev-parse HEAD) &&
	test_when_finished "git -C aur.git reset --hard $old" &&
	(
		cd aur.git &&
		sed "s/.*pkgrel.*/\\0\\nepoch = 1/" .SRCINFO >.SRCINFO.new
		mv .SRCINFO.new .SRCINFO
		git commit -q -am "Add epoch"
	) &&
	new=$(git -C aur.git rev-parse HEAD) &&
	AUR_USER=user AUR_PKGBASE=foobar AUR_PRIVILEGED=0 \
	cover "$GIT_UPDATE" refs/heads/master "$old" "$new" 2>&1 &&
	cat >expected <<-EOF &&
	2|2|foobar2|1-1|aurweb test package.|https://aur.archlinux.org/
	3|1|foobar|1:1-2|aurweb test package.|https://aur.archlinux.org/
	EOF
	echo "SELECT * FROM Packages;" | sqlite3 aur.db >actual &&
	test_cmp expected actual
'

test_expect_success 'Pushing .SRCINFO with invalid pkgname.' '
	old=$(git -C aur.git rev-parse HEAD) &&
	test_when_finished "git -C aur.git reset --hard $old" &&
	(
		cd aur.git &&
		sed "s/\(pkgname.*\)foobar/\1!/" .SRCINFO >.SRCINFO.new
		mv .SRCINFO.new .SRCINFO
		git commit -q -am "Change pkgname"
	) &&
	new=$(git -C aur.git rev-parse HEAD) &&
	test_must_fail \
	env AUR_USER=user AUR_PKGBASE=foobar AUR_PRIVILEGED=0 \
	cover "$GIT_UPDATE" refs/heads/master "$old" "$new" >actual 2>&1 &&
	grep -q "^error: invalid package name: !$" actual
'

test_expect_success 'Pushing .SRCINFO with invalid epoch.' '
	old=$(git -C aur.git rev-parse HEAD) &&
	test_when_finished "git -C aur.git reset --hard $old" &&
	(
		cd aur.git &&
		sed "s/.*pkgrel.*/\\0\\nepoch = !/" .SRCINFO >.SRCINFO.new
		mv .SRCINFO.new .SRCINFO
		git commit -q -am "Change epoch"
	) &&
	new=$(git -C aur.git rev-parse HEAD) &&
	test_must_fail \
	env AUR_USER=user AUR_PKGBASE=foobar AUR_PRIVILEGED=0 \
	cover "$GIT_UPDATE" refs/heads/master "$old" "$new" >actual 2>&1 &&
	grep -q "^error: invalid epoch: !$" actual
'

test_expect_success 'Pushing .SRCINFO with too long URL.' '
	old=$(git -C aur.git rev-parse HEAD) &&
	url="http://$(printf "%7993s" x | sed "s/ /x/g")/" &&
	test_when_finished "git -C aur.git reset --hard $old" &&
	(
		cd aur.git &&
		sed "s#.*url.*#\\0\\nurl = $url#" .SRCINFO >.SRCINFO.new
		mv .SRCINFO.new .SRCINFO
		git commit -q -am "Change URL"
	) &&
	new=$(git -C aur.git rev-parse HEAD) &&
	test_must_fail \
	env AUR_USER=user AUR_PKGBASE=foobar AUR_PRIVILEGED=0 \
	cover "$GIT_UPDATE" refs/heads/master "$old" "$new" >actual 2>&1 &&
	grep -q "^error: url field too long: $url\$" actual
'

test_expect_success 'Missing install file.' '
	old=$(git -C aur.git rev-parse HEAD) &&
	test_when_finished "git -C aur.git reset --hard $old" &&
	(
		cd aur.git &&
		sed "s/.*depends.*/\\0\\ninstall = install/" .SRCINFO >.SRCINFO.new
		mv .SRCINFO.new .SRCINFO
		git commit -q -am "Add install field"
	) &&
	new=$(git -C aur.git rev-parse HEAD) &&
	test_must_fail \
	env AUR_USER=user AUR_PKGBASE=foobar AUR_PRIVILEGED=0 \
	cover "$GIT_UPDATE" refs/heads/master "$old" "$new" >actual 2>&1 &&
	grep -q "^error: missing install file: install$" actual
'

test_expect_success 'Missing changelog file.' '
	old=$(git -C aur.git rev-parse HEAD) &&
	test_when_finished "git -C aur.git reset --hard $old" &&
	(
		cd aur.git &&
		sed "s/.*depends.*/\\0\\nchangelog = changelog/" .SRCINFO >.SRCINFO.new
		mv .SRCINFO.new .SRCINFO
		git commit -q -am "Add changelog field"
	) &&
	new=$(git -C aur.git rev-parse HEAD) &&
	test_must_fail \
	env AUR_USER=user AUR_PKGBASE=foobar AUR_PRIVILEGED=0 \
	cover "$GIT_UPDATE" refs/heads/master "$old" "$new" >actual 2>&1 &&
	grep -q "^error: missing changelog file: changelog$" actual
'

test_expect_success 'Missing source file.' '
	old=$(git -C aur.git rev-parse HEAD) &&
	test_when_finished "git -C aur.git reset --hard $old" &&
	(
		cd aur.git &&
		sed "s/.*depends.*/\\0\\nsource = file/" .SRCINFO >.SRCINFO.new
		mv .SRCINFO.new .SRCINFO
		git commit -q -am "Add file to the source array"
	) &&
	new=$(git -C aur.git rev-parse HEAD) &&
	test_must_fail \
	env AUR_USER=user AUR_PKGBASE=foobar AUR_PRIVILEGED=0 \
	cover "$GIT_UPDATE" refs/heads/master "$old" "$new" >actual 2>&1 &&
	grep -q "^error: missing source file: file$" actual
'

test_expect_success 'Pushing .SRCINFO with too long source URL.' '
	old=$(git -C aur.git rev-parse HEAD) &&
	url="http://$(printf "%7993s" x | sed "s/ /x/g")/" &&
	test_when_finished "git -C aur.git reset --hard $old" &&
	(
		cd aur.git &&
		sed "s#.*depends.*#\\0\\nsource = $url#" .SRCINFO >.SRCINFO.new
		mv .SRCINFO.new .SRCINFO
		git commit -q -am "Add huge source URL"
	) &&
	new=$(git -C aur.git rev-parse HEAD) &&
	test_must_fail \
	env AUR_USER=user AUR_PKGBASE=foobar AUR_PRIVILEGED=0 \
	cover "$GIT_UPDATE" refs/heads/master "$old" "$new" >actual 2>&1 &&
	grep -q "^error: source entry too long: $url\$" actual
'

test_expect_success 'Pushing a blacklisted package.' '
	old=$(git -C aur.git rev-parse HEAD) &&
	test_when_finished "git -C aur.git reset --hard $old" &&
	echo "pkgname = forbidden" >>aur.git/.SRCINFO &&
	git -C aur.git commit -q -am "Add blacklisted package" &&
	new=$(git -C aur.git rev-parse HEAD) &&
	cat >expected <<-EOD &&
	error: package is blacklisted: forbidden
	EOD
	test_must_fail \
	env AUR_USER=user AUR_PKGBASE=foobar AUR_PRIVILEGED=0 \
	cover "$GIT_UPDATE" refs/heads/master "$old" "$new" >actual 2>&1 &&
	test_cmp expected actual
'

test_expect_success 'Pushing a blacklisted package as Trusted User.' '
	old=$(git -C aur.git rev-parse HEAD) &&
	test_when_finished "git -C aur.git reset --hard $old" &&
	echo "pkgname = forbidden" >>aur.git/.SRCINFO &&
	git -C aur.git commit -q -am "Add blacklisted package" &&
	new=$(git -C aur.git rev-parse HEAD) &&
	cat >expected <<-EOD &&
	warning: package is blacklisted: forbidden
	EOD
	AUR_USER=tu AUR_PKGBASE=foobar AUR_PRIVILEGED=1 \
	cover "$GIT_UPDATE" refs/heads/master "$old" "$new" >actual 2>&1 &&
	test_cmp expected actual
'

test_expect_success 'Pushing a package already in the official repositories.' '
	old=$(git -C aur.git rev-parse HEAD) &&
	test_when_finished "git -C aur.git reset --hard $old" &&
	echo "pkgname = official" >>aur.git/.SRCINFO &&
	git -C aur.git commit -q -am "Add official package" &&
	new=$(git -C aur.git rev-parse HEAD) &&
	cat >expected <<-EOD &&
	error: package already provided by [core]: official
	EOD
	test_must_fail \
	env AUR_USER=user AUR_PKGBASE=foobar AUR_PRIVILEGED=0 \
	cover "$GIT_UPDATE" refs/heads/master "$old" "$new" >actual 2>&1 &&
	test_cmp expected actual
'

test_expect_success 'Pushing a package already in the official repositories as Trusted User.' '
	old=$(git -C aur.git rev-parse HEAD) &&
	test_when_finished "git -C aur.git reset --hard $old" &&
	echo "pkgname = official" >>aur.git/.SRCINFO &&
	git -C aur.git commit -q -am "Add official package" &&
	new=$(git -C aur.git rev-parse HEAD) &&
	cat >expected <<-EOD &&
	warning: package already provided by [core]: official
	EOD
	AUR_USER=tu AUR_PKGBASE=foobar AUR_PRIVILEGED=1 \
	cover "$GIT_UPDATE" refs/heads/master "$old" "$new" >actual 2>&1 &&
	test_cmp expected actual
'

test_expect_success 'Trying to hijack a package.' '
	old=0000000000000000000000000000000000000000 &&
	test_when_finished "git -C aur.git checkout refs/namespaces/foobar/refs/heads/master" &&
	(
		cd aur.git &&
		git checkout -q refs/namespaces/foobar2/refs/heads/master &&
		sed "s/\\(.*pkgname.*\\)2/\\1/" .SRCINFO >.SRCINFO.new
		mv .SRCINFO.new .SRCINFO
		git commit -q -am "Change package name"
	) &&
	new=$(git -C aur.git rev-parse HEAD) &&
	cat >expected <<-EOD &&
	error: cannot overwrite package: foobar
	EOD
	test_must_fail \
	env AUR_USER=user AUR_PKGBASE=foobar2 AUR_PRIVILEGED=0 \
	cover "$GIT_UPDATE" refs/heads/master "$old" "$new" >actual 2>&1 &&
	test_cmp expected actual
'

test_done
