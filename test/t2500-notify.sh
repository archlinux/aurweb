#!/bin/sh

test_description='notify tests'

. ./setup.sh

test_expect_success 'Test out-of-date notifications.' '
	cat <<-EOD | sqlite3 aur.db &&
	INSERT INTO PackageBases (ID, Name, MaintainerUID, SubmittedTS, ModifiedTS) VALUES (1, "foobar", 1, 0, 0);
	INSERT INTO PackageBases (ID, Name, MaintainerUID, SubmittedTS, ModifiedTS) VALUES (2, "foobar2", 2, 0, 0);
	INSERT INTO PackageBases (ID, Name, MaintainerUID, SubmittedTS, ModifiedTS) VALUES (3, "foobar3", NULL, 0, 0);
	INSERT INTO PackageBases (ID, Name, MaintainerUID, SubmittedTS, ModifiedTS) VALUES (4, "foobar4", 1, 0, 0);
	INSERT INTO PackageComaintainers (PackageBaseID, UsersID, Priority) VALUES (1, 2, 1);
	INSERT INTO PackageComaintainers (PackageBaseID, UsersID, Priority) VALUES (1, 4, 2);
	INSERT INTO PackageComaintainers (PackageBaseID, UsersID, Priority) VALUES (2, 3, 1);
	INSERT INTO PackageComaintainers (PackageBaseID, UsersID, Priority) VALUES (2, 5, 2);
	INSERT INTO PackageComaintainers (PackageBaseID, UsersID, Priority) VALUES (3, 4, 1);
	EOD
	>sendmail.out &&
	"$NOTIFY" flag 1 1 &&
	cat <<-EOD >expected &&
	Subject: AUR Out-of-date Notification for foobar
	To: tu@localhost
	Subject: AUR Out-of-date Notification for foobar
	To: user2@localhost
	Subject: AUR Out-of-date Notification for foobar
	To: user@localhost
	EOD
	grep "^\(Subject\|To\)" sendmail.out >sendmail.parts &&
	test_cmp sendmail.parts expected
'

test_done
