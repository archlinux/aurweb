#!/bin/sh

test_description='pkgmaint tests'

. "$(dirname "$0")/setup.sh"

test_expect_success 'Test package base cleanup script.' '
	now=$(date -d now +%s) &&
	threedaysago=$(date -d "3 days ago" +%s) &&
	cat <<-EOD | sqlite3 aur.db &&
	INSERT INTO PackageBases (ID, Name, PackagerUID, SubmittedTS, ModifiedTS, FlaggerComment) VALUES (1, "foobar", 1, $now, 0, "");
	INSERT INTO PackageBases (ID, Name, PackagerUID, SubmittedTS, ModifiedTS, FlaggerComment) VALUES (2, "foobar2", 2, $threedaysago, 0, "");
	INSERT INTO PackageBases (ID, Name, PackagerUID, SubmittedTS, ModifiedTS, FlaggerComment) VALUES (3, "foobar3", NULL, $now, 0, "");
	INSERT INTO PackageBases (ID, Name, PackagerUID, SubmittedTS, ModifiedTS, FlaggerComment) VALUES (4, "foobar4", NULL, $threedaysago, 0, "");
	EOD
	cover "$PKGMAINT" &&
	cat <<-EOD >expected &&
	foobar
	foobar2
	foobar3
	EOD
	echo "SELECT Name FROM PackageBases;" | sqlite3 aur.db >actual &&
	test_cmp actual expected
'

test_done
