#!/bin/sh

test_description='aurblup tests'

. "$(dirname "$0")/setup.sh"

test_expect_success 'Test official provider update script.' '
	mkdir -p remote/test/foobar-1.0-1 &&
	cat <<-EOD >remote/test/foobar-1.0-1/desc &&
	%FILENAME%
	foobar-1.0-any.pkg.tar.xz

	%NAME%
	foobar

	%VERSION%
	1.0-1

	%ARCH%
	any
	EOD
	mkdir -p remote/test/foobar2-1.0-1 &&
	cat <<-EOD >remote/test/foobar2-1.0-1/desc &&
	%FILENAME%
	foobar2-1.0-any.pkg.tar.xz

	%NAME%
	foobar2

	%VERSION%
	1.0-1

	%ARCH%
	any

	%PROVIDES%
	foobar3
	foobar4
	EOD
	( cd remote/test && bsdtar -czf ../test.db * ) &&
	mkdir sync &&
	cover "$AURBLUP" &&
	cat <<-EOD >expected &&
	foobar|test|foobar
	foobar2|test|foobar2
	foobar2|test|foobar3
	foobar2|test|foobar4
	EOD
	echo "SELECT Name, Repo, Provides FROM OfficialProviders ORDER BY Provides;" | sqlite3 aur.db >actual &&
	test_cmp actual expected
'

test_done
