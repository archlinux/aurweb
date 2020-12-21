#!/bin/sh

test_description='mkpkglists tests'

. "$(dirname "$0")/setup.sh"

test_expect_success 'Test package list generation with no packages.' '
	echo "DELETE FROM Packages;" | sqlite3 aur.db &&
	echo "DELETE FROM PackageBases;" | sqlite3 aur.db &&
	cover "$MKPKGLISTS" &&
	test $(zcat packages.gz | wc -l) -eq 1 &&
	test $(zcat pkgbase.gz | wc -l) -eq 1
'

test_expect_success 'Test package list generation.' '
	cat <<-EOD | sqlite3 aur.db &&
	INSERT INTO PackageBases (ID, Name, PackagerUID, SubmittedTS, ModifiedTS, FlaggerComment) VALUES (1, "foobar", 1, 0, 0, "");
	INSERT INTO PackageBases (ID, Name, PackagerUID, SubmittedTS, ModifiedTS, FlaggerComment) VALUES (2, "foobar2", 2, 0, 0, "");
	INSERT INTO PackageBases (ID, Name, PackagerUID, SubmittedTS, ModifiedTS, FlaggerComment) VALUES (3, "foobar3", NULL, 0, 0, "");
	INSERT INTO PackageBases (ID, Name, PackagerUID, SubmittedTS, ModifiedTS, FlaggerComment) VALUES (4, "foobar4", 1, 0, 0, "");
	INSERT INTO Packages (ID, PackageBaseID, Name) VALUES (1, 1, "pkg1");
	INSERT INTO Packages (ID, PackageBaseID, Name) VALUES (2, 1, "pkg2");
	INSERT INTO Packages (ID, PackageBaseID, Name) VALUES (3, 1, "pkg3");
	INSERT INTO Packages (ID, PackageBaseID, Name) VALUES (4, 2, "pkg4");
	INSERT INTO Packages (ID, PackageBaseID, Name) VALUES (5, 3, "pkg5");
	EOD
	cover "$MKPKGLISTS" &&
	cat <<-EOD >expected &&
	foobar
	foobar2
	foobar4
	EOD
	gunzip pkgbase.gz &&
	sed "/^#/d" pkgbase >actual &&
	test_cmp actual expected &&
	cat <<-EOD >expected &&
	pkg1
	pkg2
	pkg3
	pkg4
	EOD
	gunzip packages.gz &&
	sed "/^#/d" packages >actual &&
	test_cmp actual expected
'

test_expect_success 'Test user list generation.' '
	cover "$MKPKGLISTS" &&
	cat <<-EOD >expected &&
	dev
	tu
	tu2
	tu3
	tu4
	user
	user2
	user3
	user4
	EOD
	gunzip users.gz &&
	sed "/^#/d" users >actual &&
	test_cmp actual expected
'

test_done
