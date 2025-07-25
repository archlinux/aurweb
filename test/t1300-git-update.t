#!/bin/sh

test_description='git-update tests'

. "$(dirname "$0")/setup.sh"

pkgctl_executable="$(awk -F " " -e "/pkgctl_executable/ { print \$3 }" "${AUR_CONFIG}")"

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

test_expect_success 'Performing a non-fast-forward ref update as Package Maintainer.' '
	old=$(git -C aur.git rev-parse HEAD) &&
	new=$(git -C aur.git rev-parse HEAD^) &&
	cat >expected <<-EOD &&
	error: denying non-fast-forward (you should pull first)
	EOD
	test_must_fail \
	env AUR_USER=pm AUR_PKGBASE=foobar AUR_PRIVILEGED=1 \
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

test_expect_success 'Performing a non-fast-forward ref update as Package Maintainer with AUR_OVERWRITE=1.' '
	old=$(git -C aur.git rev-parse HEAD) &&
	new=$(git -C aur.git rev-parse HEAD^) &&
	AUR_USER=pm AUR_PKGBASE=foobar AUR_PRIVILEGED=1 AUR_OVERWRITE=1 \
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
	env AUR_USER=user AUR_PKGBASE=foobar AUR_PRIVILEGED=0 \
	cover "$GIT_UPDATE" refs/heads/master "$old" "$new" 2>&1
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

test_expect_success 'Pushing a tree with a forbidden subdirectory.' '
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

test_expect_success 'Pushing a tree with an allowed subdirectory for pgp keys; wrong files.' '
	old=$(git -C aur.git rev-parse HEAD) &&
	test_when_finished "git -C aur.git reset --hard $old" &&
	mkdir -p aur.git/keys/pgp/ &&
	touch aur.git/keys/pgp/nonsense &&
	git -C aur.git add keys/pgp/nonsense &&
	git -C aur.git commit -q -m "Add some nonsense" &&
	new=$(git -C aur.git rev-parse HEAD) &&
	test_must_fail \
	env AUR_USER=user AUR_PKGBASE=foobar AUR_PRIVILEGED=0 \
	cover "$GIT_UPDATE" refs/heads/master "$old" "$new" >actual 2>&1 &&
	grep -q "^error: the subdir may only contain .asc (PGP pub key) files$" actual
'

test_expect_success 'Pushing a tree with an allowed subdirectory for pgp keys; another subdir.' '
	old=$(git -C aur.git rev-parse HEAD) &&
	test_when_finished "git -C aur.git reset --hard $old" &&
	mkdir -p aur.git/keys/pgp/bla/ &&
	touch aur.git/keys/pgp/bla/x.asc &&
	git -C aur.git add keys/pgp/bla/x.asc &&
	git -C aur.git commit -q -m "Add some nonsense" &&
	new=$(git -C aur.git rev-parse HEAD) &&
	test_must_fail \
	env AUR_USER=user AUR_PKGBASE=foobar AUR_PRIVILEGED=0 \
	cover "$GIT_UPDATE" refs/heads/master "$old" "$new" >actual 2>&1 &&
	grep -q "^error: the subdir may only contain .asc (PGP pub key) files$" actual
'

test_expect_success 'Pushing a tree with an allowed subdirectory for pgp keys; wrong subdir.' '
	old=$(git -C aur.git rev-parse HEAD) &&
	test_when_finished "git -C aur.git reset --hard $old" &&
	mkdir -p aur.git/keys/xyz/ &&
	touch aur.git/keys/xyz/x.asc &&
	git -C aur.git add keys/xyz/x.asc &&
	git -C aur.git commit -q -m "Add some nonsense" &&
	new=$(git -C aur.git rev-parse HEAD) &&
	test_must_fail \
	env AUR_USER=user AUR_PKGBASE=foobar AUR_PRIVILEGED=0 \
	cover "$GIT_UPDATE" refs/heads/master "$old" "$new" >actual 2>&1 &&
	grep -q "^error: the keys/ subdir may only contain a pgp/ directory$" actual
'

test_expect_success 'Pushing a tree with an allowed subdirectory with pgp keys; additional files' '
	old=$(git -C aur.git rev-parse HEAD) &&
	test_when_finished "git -C aur.git reset --hard $old" &&
	mkdir -p aur.git/keys/pgp/ &&
	touch aur.git/keys/pgp/x.asc &&
	touch aur.git/keys/nonsense &&
	git -C aur.git add keys/pgp/x.asc &&
	git -C aur.git add keys/nonsense &&
	git -C aur.git commit -q -m "Add pgp key" &&
	new=$(git -C aur.git rev-parse HEAD) &&
	test_must_fail \
	env AUR_USER=user AUR_PKGBASE=foobar AUR_PRIVILEGED=0 \
	cover "$GIT_UPDATE" refs/heads/master "$old" "$new" >actual 2>&1 &&
	grep -q "^error: the keys/ subdir may only contain a pgp/ directory$" actual
'

test_expect_success 'Pushing a tree with an allowed subdirectory with pgp keys; additional subdir' '
	old=$(git -C aur.git rev-parse HEAD) &&
	test_when_finished "git -C aur.git reset --hard $old" &&
	mkdir -p aur.git/keys/pgp/ &&
	mkdir -p aur.git/somedir/ &&
	touch aur.git/keys/pgp/x.asc &&
	touch aur.git/somedir/nonsense &&
	git -C aur.git add keys/pgp/x.asc &&
	git -C aur.git add somedir/nonsense &&
	git -C aur.git commit -q -m "Add pgp key" &&
	new=$(git -C aur.git rev-parse HEAD) &&
	test_must_fail \
	env AUR_USER=user AUR_PKGBASE=foobar AUR_PRIVILEGED=0 \
	cover "$GIT_UPDATE" refs/heads/master "$old" "$new" >actual 2>&1 &&
	grep -q "^error: the repository must not contain subdirectories$" actual
'

test_expect_success 'Pushing a tree with an allowed subdirectory with pgp keys; keys to large' '
	old=$(git -C aur.git rev-parse HEAD) &&
	test_when_finished "git -C aur.git reset --hard $old" &&
	mkdir -p aur.git/keys/pgp/ &&
	printf "%256001s" x > aur.git/keys/pgp/x.asc &&
	git -C aur.git add keys/pgp/x.asc &&
	git -C aur.git commit -q -m "Add pgp key" &&
	new=$(git -C aur.git rev-parse HEAD) &&
	test_must_fail \
	env AUR_USER=user AUR_PKGBASE=foobar AUR_PRIVILEGED=0 \
	cover "$GIT_UPDATE" refs/heads/master "$old" "$new" >actual 2>&1 &&
	grep -q "^error: maximum blob size (250.00KiB) exceeded$" actual
'

test_expect_success 'Pushing a tree with an allowed subdirectory with pgp keys.' '
	old=$(git -C aur.git rev-parse HEAD) &&
	test_when_finished "git -C aur.git reset --hard $old" &&
	mkdir -p aur.git/keys/pgp/ &&
	touch aur.git/keys/pgp/x.asc &&
	git -C aur.git add keys/pgp/x.asc &&
	git -C aur.git commit -q -m "Add pgp key" &&
	new=$(git -C aur.git rev-parse HEAD) &&
	env AUR_USER=user AUR_PKGBASE=foobar AUR_PRIVILEGED=0 \
	cover "$GIT_UPDATE" refs/heads/master "$old" "$new" 2>&1
'

test_expect_success 'Pushing a tree with an allowed subdirectory for RFC52-style licenses; wrong files.' '
	old=$(git -C aur.git rev-parse HEAD) &&
	test_when_finished "git -C aur.git reset --hard $old" &&
	"${pkgctl_executable}" license setup --no-check aur.git 2>/dev/null &&
	touch aur.git/bad.md aur.git/LICENSES/Nonsense-2.0-or-later.txt &&
	reuse annotate -c "Copyright" -l Nonsense-2.0-or-later aur.git/bad.md >/dev/null 2>&1 &&
	git -C aur.git add bad.md LICENSE LICENSES REUSE.toml &&
	git -C aur.git commit -q -m "Add REUSE files with unacceptable license" &&
	new=$(git -C aur.git rev-parse HEAD) &&
	test_must_fail \
	env AUR_USER=user AUR_PKGBASE=foobar AUR_PRIVILEGED=0 \
	cover "$GIT_UPDATE" refs/heads/master "$old" "$new" >actual 2>&1 &&
	grep -q "^\\* Bad licenses: Nonsense-2.0-or-later$" actual
'

test_expect_success 'Pushing a tree with an allowed subdirectory for RFC52-style licenses; missing file extension.' '
	old=$(git -C aur.git rev-parse HEAD) &&
	test_when_finished "git -C aur.git reset --hard $old" &&
	"${pkgctl_executable}" license setup --no-check aur.git 2>/dev/null &&
	touch aur.git/LICENSES/GPL-3.0-or-later &&
	git -C aur.git add LICENSE LICENSES REUSE.toml &&
	git -C aur.git commit -q -m "Add file with no extension" &&
	new=$(git -C aur.git rev-parse HEAD) &&
	test_must_fail \
	env AUR_USER=user AUR_PKGBASE=foobar AUR_PRIVILEGED=0 \
	cover "$GIT_UPDATE" refs/heads/master "$old" "$new" >actual 2>&1 &&
	grep -q "^\\* Licenses without file extension: GPL-3.0-or-later$" actual
'

test_expect_success 'Pushing a tree with an allowed subdirectory for RFC52-style licenses; missing LICENSE file.' '
	old=$(git -C aur.git rev-parse HEAD) &&
	test_when_finished "git -C aur.git reset --hard $old" &&
	"${pkgctl_executable}" license setup --no-check aur.git 2>/dev/null &&
	rm aur.git/LICENSE &&
	git -C aur.git add LICENSES REUSE.toml
	git -C aur.git commit -q -m "Add license files, REUSE.toml" &&
	new=$(git -C aur.git rev-parse HEAD) &&
	test_must_fail \
	env AUR_USER=user AUR_PKGBASE=foobar AUR_PRIVILEGED=0 \
	cover "$GIT_UPDATE" refs/heads/master "$old" "$new" >actual 2>&1 &&
	grep -q "foobar: is missing the LICENSE file$" actual
'

test_expect_success 'Pushing a tree with an allowed subdirectory for RFC52-style licenses; unused license.' '
	old=$(git -C aur.git rev-parse HEAD) &&
	test_when_finished "git -C aur.git reset --hard $old" &&
	"${pkgctl_executable}" license setup --no-check aur.git 2>/dev/null &&
	touch aur.git/LICENSES/GPL-3.0-or-later.txt &&
	git -C aur.git add LICENSE LICENSES REUSE.toml &&
	git -C aur.git commit -q -m "Add REUSE files with unused license" &&
	new=$(git -C aur.git rev-parse HEAD) &&
	test_must_fail \
	env AUR_USER=user AUR_PKGBASE=foobar AUR_PRIVILEGED=0 \
	cover "$GIT_UPDATE" refs/heads/master "$old" "$new" >actual 2>&1 &&
	grep -q "^\\* Unused licenses: GPL-3.0-or-later$" actual
'

test_expect_success 'Pushing a tree with an allowed subdirectory for RFC52-style licenses; another subdir.' '
	old=$(git -C aur.git rev-parse HEAD) &&
	test_when_finished "git -C aur.git reset --hard $old" &&
	"${pkgctl_executable}" license setup --no-check aur.git 2>/dev/null &&
	mkdir -p aur.git/LICENSES/bla/ &&
	touch aur.git/LICENSES/bla/LicenseRef-EULA.txt &&
	git -C aur.git add LICENSE LICENSES REUSE.toml &&
	git -C aur.git commit -q -m "Add REUSE files with nonsense subdirectory" &&
	new=$(git -C aur.git rev-parse HEAD) &&
	test_must_fail \
	env AUR_USER=user AUR_PKGBASE=foobar AUR_PRIVILEGED=0 \
	cover "$GIT_UPDATE" refs/heads/master "$old" "$new" >actual 2>&1 &&
	grep -q "^error: the subdir may only contain files$" actual
'

test_expect_success 'Pushing a tree with an allowed subdirectory with RFC52-style licenses.' '
	old=$(git -C aur.git rev-parse HEAD) &&
	test_when_finished "git -C aur.git reset --hard $old" &&
	"${pkgctl_executable}" license setup --no-check aur.git 2>/dev/null &&
	touch aur.git/multiply-licensed-document.md &&
	reuse annotate -c "Copyright" -l Apache-2.0 -l Classpath-exception-2.0 -l GPL-2.0-only -l LicenseRef-EULA aur.git/multiply-licensed-document.md >/dev/null 2>&1 &&
	touch aur.git/LICENSES/{Apache-2.0,Classpath-exception-2.0,GPL-2.0-only,LicenseRef-EULA}.txt &&
	git -C aur.git add multiply-licensed-document.md LICENSE LICENSES REUSE.toml &&
	git -C aur.git commit -q -m "Add license files according to REUSE" &&
	new=$(git -C aur.git rev-parse HEAD) &&
	env AUR_USER=user AUR_PKGBASE=foobar AUR_PRIVILEGED=0 \
	cover "$GIT_UPDATE" refs/heads/master "$old" "$new" 2>&1
'

test_expect_success 'Pushing a tree with a large blob.' '
	old=$(git -C aur.git rev-parse HEAD) &&
	test_when_finished "git -C aur.git reset --hard $old" &&
	printf "%256001s" x >aur.git/file &&
	git -C aur.git add file &&
	git -C aur.git commit -q -m "Add large blob" &&
	first_error=$(git -C aur.git rev-parse HEAD) &&
	touch aur.git/another.file &&
	git -C aur.git add another.file &&
	git -C aur.git commit -q -m "Add another commit" &&
	new=$(git -C aur.git rev-parse HEAD) &&
	test_must_fail \
	env AUR_USER=user AUR_PKGBASE=foobar AUR_PRIVILEGED=0 \
	cover "$GIT_UPDATE" refs/heads/master "$old" "$new" >actual 2>&1 &&
	grep -q "^error: maximum blob size (250.00KiB) exceeded$" actual &&
	grep -q "^error: $first_error:$" actual
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

test_expect_success 'Pushing a blacklisted pkgbase.' '
	test_when_finished "git -C aur.git checkout refs/namespaces/foobar/refs/heads/master" &&
	git -C aur.git checkout -q refs/namespaces/forbidden/refs/heads/master &&
	old=$(git -C aur.git rev-parse HEAD) &&
	echo " " >>aur.git/.SRCINFO &&
	git -C aur.git commit -q -am "Do something" &&
	new=$(git -C aur.git rev-parse HEAD) &&
	cat >expected <<-EOD &&
	error: pkgbase is blacklisted: forbidden
	EOD
	test_must_fail \
	env AUR_USER=user AUR_PKGBASE=forbidden AUR_PRIVILEGED=0 \
	cover "$GIT_UPDATE" refs/heads/master "$old" "$new" >actual 2>&1 &&
	test_cmp expected actual
'

test_expect_success 'Pushing a blacklisted package as Package Maintainer.' '
	old=$(git -C aur.git rev-parse HEAD) &&
	test_when_finished "git -C aur.git reset --hard $old" &&
	echo "pkgname = forbidden" >>aur.git/.SRCINFO &&
	git -C aur.git commit -q -am "Add blacklisted package" &&
	new=$(git -C aur.git rev-parse HEAD) &&
	cat >expected <<-EOD &&
	warning: package is blacklisted: forbidden
	EOD
	AUR_USER=pm AUR_PKGBASE=foobar AUR_PRIVILEGED=1 \
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

test_expect_success 'Pushing a package already in the official repositories as Package Maintainer.' '
	old=$(git -C aur.git rev-parse HEAD) &&
	test_when_finished "git -C aur.git reset --hard $old" &&
	echo "pkgname = official" >>aur.git/.SRCINFO &&
	git -C aur.git commit -q -am "Add official package" &&
	new=$(git -C aur.git rev-parse HEAD) &&
	cat >expected <<-EOD &&
	warning: package already provided by [core]: official
	EOD
	AUR_USER=pm AUR_PKGBASE=foobar AUR_PRIVILEGED=1 \
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
