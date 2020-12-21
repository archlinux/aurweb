#!/bin/sh

test_description='notify tests'

. "$(dirname "$0")/setup.sh"

test_expect_success 'Test out-of-date notifications.' '
	cat <<-EOD | sqlite3 aur.db &&
	/* Use package base IDs which can be distinguished from user IDs. */
	INSERT INTO PackageBases (ID, Name, MaintainerUID, SubmittedTS, ModifiedTS, FlaggerComment) VALUES (1001, "foobar", 1, 0, 0, "This is a test OOD comment.");
	INSERT INTO PackageBases (ID, Name, MaintainerUID, SubmittedTS, ModifiedTS, FlaggerComment) VALUES (1002, "foobar2", 2, 0, 0, "");
	INSERT INTO PackageBases (ID, Name, MaintainerUID, SubmittedTS, ModifiedTS, FlaggerComment) VALUES (1003, "foobar3", NULL, 0, 0, "");
	INSERT INTO PackageBases (ID, Name, MaintainerUID, SubmittedTS, ModifiedTS, FlaggerComment) VALUES (1004, "foobar4", 1, 0, 0, "");
	INSERT INTO PackageComaintainers (PackageBaseID, UsersID, Priority) VALUES (1001, 2, 1);
	INSERT INTO PackageComaintainers (PackageBaseID, UsersID, Priority) VALUES (1001, 4, 2);
	INSERT INTO PackageComaintainers (PackageBaseID, UsersID, Priority) VALUES (1002, 3, 1);
	INSERT INTO PackageComaintainers (PackageBaseID, UsersID, Priority) VALUES (1002, 5, 2);
	INSERT INTO PackageComaintainers (PackageBaseID, UsersID, Priority) VALUES (1003, 4, 1);
	EOD
	>sendmail.out &&
	cover "$NOTIFY" flag 1 1001 &&
	cat <<-EOD >expected &&
	Subject: AUR Out-of-date Notification for foobar
	To: tu@localhost
	Subject: AUR Out-of-date Notification for foobar
	To: user2@localhost
	Subject: AUR Out-of-date Notification for foobar
	To: user@localhost
	EOD
	grep "^\(Subject\|To\)" sendmail.out >sendmail.parts &&
	test_cmp sendmail.parts expected &&
	cat <<-EOD | sqlite3 aur.db
	DELETE FROM PackageComaintainers;
	EOD
'

test_expect_success 'Test subject and body of reset key notifications.' '
	cat <<-EOD | sqlite3 aur.db &&
	UPDATE Users SET ResetKey = "12345678901234567890123456789012" WHERE ID = 1;
	EOD
	>sendmail.out &&
	cover "$NOTIFY" send-resetkey 1 &&
	grep ^Subject: sendmail.out >actual &&
	cat <<-EOD >expected &&
	Subject: AUR Password Reset
	EOD
	test_cmp actual expected &&
	sed -n "/^\$/,\$p" sendmail.out | base64 -d >actual &&
	echo >>actual &&
	cat <<-EOD >expected &&
	A password reset request was submitted for the account user associated
	with your email address. If you wish to reset your password follow the
	link [1] below, otherwise ignore this message and nothing will happen.

	[1] https://aur.archlinux.org/passreset/?resetkey=12345678901234567890123456789012
	EOD
	test_cmp actual expected
'

test_expect_success 'Test subject and body of welcome notifications.' '
	cat <<-EOD | sqlite3 aur.db &&
	UPDATE Users SET ResetKey = "12345678901234567890123456789012" WHERE ID = 1;
	EOD
	>sendmail.out &&
	cover "$NOTIFY" welcome 1 &&
	grep ^Subject: sendmail.out >actual &&
	cat <<-EOD >expected &&
	Subject: Welcome to the Arch User Repository
	EOD
	test_cmp actual expected &&
	sed -n "/^\$/,\$p" sendmail.out | base64 -d >actual &&
	echo >>actual &&
	cat <<-EOD >expected &&
	Welcome to the Arch User Repository! In order to set an initial
	password for your new account, please click the link [1] below. If the
	link does not work, try copying and pasting it into your browser.

	[1] https://aur.archlinux.org/passreset/?resetkey=12345678901234567890123456789012
	EOD
	test_cmp actual expected
'

test_expect_success 'Test subject and body of comment notifications.' '
	cat <<-EOD | sqlite3 aur.db &&
	/* Use package comments IDs which can be distinguished from other IDs. */
	INSERT INTO PackageComments (ID, PackageBaseID, UsersID, Comments, RenderedComment) VALUES (2001, 1001, 1, "This is a test comment.", "This is a test comment.");
	INSERT INTO PackageNotifications (PackageBaseID, UserID) VALUES (1001, 2);
	UPDATE Users SET CommentNotify = 1 WHERE ID = 2;
	EOD
	>sendmail.out &&
	cover "$NOTIFY" comment 1 1001 2001 &&
	grep ^Subject: sendmail.out >actual &&
	cat <<-EOD >expected &&
	Subject: AUR Comment for foobar
	EOD
	test_cmp actual expected &&
	sed -n "/^\$/,\$p" sendmail.out | base64 -d >actual &&
	echo >>actual &&
	cat <<-EOD >expected &&
	user [1] added the following comment to foobar [2]:

	This is a test comment.

	-- 
	If you no longer wish to receive notifications about this package,
	please go to the package page [2] and select "Disable notifications".
	
	[1] https://aur.archlinux.org/account/user/
	[2] https://aur.archlinux.org/pkgbase/foobar/
	EOD
	test_cmp actual expected
'

test_expect_success 'Test subject and body of update notifications.' '
	cat <<-EOD | sqlite3 aur.db &&
	UPDATE Users SET UpdateNotify = 1 WHERE ID = 2;
	EOD
	>sendmail.out &&
	cover "$NOTIFY" update 1 1001 &&
	grep ^Subject: sendmail.out >actual &&
	cat <<-EOD >expected &&
	Subject: AUR Package Update: foobar
	EOD
	test_cmp actual expected &&
	sed -n "/^\$/,\$p" sendmail.out | base64 -d >actual &&
	echo >>actual &&
	cat <<-EOD >expected &&
	user [1] pushed a new commit to foobar [2].

	-- 
	If you no longer wish to receive notifications about this package,
	please go to the package page [2] and select "Disable notifications".

	[1] https://aur.archlinux.org/account/user/
	[2] https://aur.archlinux.org/pkgbase/foobar/
	EOD
	test_cmp actual expected
'

test_expect_success 'Test subject and body of out-of-date notifications.' '
	>sendmail.out &&
	cover "$NOTIFY" flag 1 1001 &&
	grep ^Subject: sendmail.out >actual &&
	cat <<-EOD >expected &&
	Subject: AUR Out-of-date Notification for foobar
	EOD
	test_cmp actual expected &&
	sed -n "/^\$/,\$p" sendmail.out | base64 -d >actual &&
	echo >>actual &&
	cat <<-EOD >expected &&
	Your package foobar [1] has been flagged out-of-date by user [2]:

	This is a test OOD comment.

	[1] https://aur.archlinux.org/pkgbase/foobar/
	[2] https://aur.archlinux.org/account/user/
	EOD
	test_cmp actual expected
'

test_expect_success 'Test subject and body of adopt notifications.' '
	>sendmail.out &&
	cover "$NOTIFY" adopt 1 1001 &&
	grep ^Subject: sendmail.out >actual &&
	cat <<-EOD >expected &&
	Subject: AUR Ownership Notification for foobar
	EOD
	test_cmp actual expected &&
	sed -n "/^\$/,\$p" sendmail.out | base64 -d >actual &&
	echo >>actual &&
	cat <<-EOD >expected &&
	The package foobar [1] was adopted by user [2].

	[1] https://aur.archlinux.org/pkgbase/foobar/
	[2] https://aur.archlinux.org/account/user/
	EOD
	test_cmp actual expected
'

test_expect_success 'Test subject and body of disown notifications.' '
	>sendmail.out &&
	cover "$NOTIFY" disown 1 1001 &&
	grep ^Subject: sendmail.out >actual &&
	cat <<-EOD >expected &&
	Subject: AUR Ownership Notification for foobar
	EOD
	test_cmp actual expected &&
	sed -n "/^\$/,\$p" sendmail.out | base64 -d >actual &&
	echo >>actual &&
	cat <<-EOD >expected &&
	The package foobar [1] was disowned by user [2].

	[1] https://aur.archlinux.org/pkgbase/foobar/
	[2] https://aur.archlinux.org/account/user/
	EOD
	test_cmp actual expected
'

test_expect_success 'Test subject and body of co-maintainer addition notifications.' '
	>sendmail.out &&
	cover "$NOTIFY" comaintainer-add 1 1001 &&
	grep ^Subject: sendmail.out >actual &&
	cat <<-EOD >expected &&
	Subject: AUR Co-Maintainer Notification for foobar
	EOD
	test_cmp actual expected &&
	sed -n "/^\$/,\$p" sendmail.out | base64 -d >actual &&
	echo >>actual &&
	cat <<-EOD >expected &&
	You were added to the co-maintainer list of foobar [1].

	[1] https://aur.archlinux.org/pkgbase/foobar/
	EOD
	test_cmp actual expected
'

test_expect_success 'Test subject and body of co-maintainer removal notifications.' '
	>sendmail.out &&
	cover "$NOTIFY" comaintainer-remove 1 1001 &&
	grep ^Subject: sendmail.out >actual &&
	cat <<-EOD >expected &&
	Subject: AUR Co-Maintainer Notification for foobar
	EOD
	test_cmp actual expected &&
	sed -n "/^\$/,\$p" sendmail.out | base64 -d >actual &&
	echo >>actual &&
	cat <<-EOD >expected &&
	You were removed from the co-maintainer list of foobar [1].

	[1] https://aur.archlinux.org/pkgbase/foobar/
	EOD
	test_cmp actual expected
'

test_expect_success 'Test subject and body of delete notifications.' '
	>sendmail.out &&
	cover "$NOTIFY" delete 1 1001 &&
	grep ^Subject: sendmail.out >actual &&
	cat <<-EOD >expected &&
	Subject: AUR Package deleted: foobar
	EOD
	test_cmp actual expected &&
	sed -n "/^\$/,\$p" sendmail.out | base64 -d >actual &&
	echo >>actual &&
	cat <<-EOD >expected &&
	user [1] deleted foobar [2].

	You will no longer receive notifications about this package.

	[1] https://aur.archlinux.org/account/user/
	[2] https://aur.archlinux.org/pkgbase/foobar/
	EOD
	test_cmp actual expected
'

test_expect_success 'Test subject and body of merge notifications.' '
	>sendmail.out &&
	cover "$NOTIFY" delete 1 1001 1002 &&
	grep ^Subject: sendmail.out >actual &&
	cat <<-EOD >expected &&
	Subject: AUR Package deleted: foobar
	EOD
	test_cmp actual expected &&
	sed -n "/^\$/,\$p" sendmail.out | base64 -d >actual &&
	echo >>actual &&
	cat <<-EOD >expected &&
	user [1] merged foobar [2] into foobar2 [3].

	-- 
	If you no longer wish receive notifications about the new package,
	please go to [3] and click "Disable notifications".

	[1] https://aur.archlinux.org/account/user/
	[2] https://aur.archlinux.org/pkgbase/foobar/
	[3] https://aur.archlinux.org/pkgbase/foobar2/
	EOD
	test_cmp actual expected
'

test_expect_success 'Test Cc, subject and body of request open notifications.' '
	cat <<-EOD | sqlite3 aur.db &&
	/* Use package request IDs which can be distinguished from other IDs. */
	INSERT INTO PackageRequests (ID, PackageBaseID, PackageBaseName, UsersID, ReqTypeID, Comments, ClosureComment) VALUES (3001, 1001, "foobar", 2, 1, "This is a request test comment.", "");
	EOD
	>sendmail.out &&
	cover "$NOTIFY" request-open 1 3001 orphan 1001 &&
	grep ^Cc: sendmail.out >actual &&
	cat <<-EOD >expected &&
	Cc: user@localhost, tu@localhost
	EOD
	test_cmp actual expected &&
	grep ^Subject: sendmail.out >actual &&
	cat <<-EOD >expected &&
	Subject: [PRQ#3001] Orphan Request for foobar
	EOD
	test_cmp actual expected &&
	sed -n "/^\$/,\$p" sendmail.out | base64 -d >actual &&
	echo >>actual &&
	cat <<-EOD >expected &&
	user [1] filed an orphan request for foobar [2]:

	This is a request test comment.

	[1] https://aur.archlinux.org/account/user/
	[2] https://aur.archlinux.org/pkgbase/foobar/
	EOD
	test_cmp actual expected
'

test_expect_success 'Test subject and body of request open notifications for merge requests.' '
	>sendmail.out &&
	cover "$NOTIFY" request-open 1 3001 merge 1001 foobar2 &&
	grep ^Subject: sendmail.out >actual &&
	cat <<-EOD >expected &&
	Subject: [PRQ#3001] Merge Request for foobar
	EOD
	test_cmp actual expected &&
	sed -n "/^\$/,\$p" sendmail.out | base64 -d >actual &&
	echo >>actual &&
	cat <<-EOD >expected &&
	user [1] filed a request to merge foobar [2] into foobar2 [3]:

	This is a request test comment.

	[1] https://aur.archlinux.org/account/user/
	[2] https://aur.archlinux.org/pkgbase/foobar/
	[3] https://aur.archlinux.org/pkgbase/foobar2/
	EOD
	test_cmp actual expected
'

test_expect_success 'Test Cc, subject and body of request close notifications.' '
	>sendmail.out &&
	cover "$NOTIFY" request-close 1 3001 accepted &&
	grep ^Cc: sendmail.out >actual &&
	cat <<-EOD >expected &&
	Cc: user@localhost, tu@localhost
	EOD
	test_cmp actual expected &&
	grep ^Subject: sendmail.out >actual &&
	cat <<-EOD >expected &&
	Subject: [PRQ#3001] Deletion Request for foobar Accepted
	EOD
	test_cmp actual expected &&
	sed -n "/^\$/,\$p" sendmail.out | base64 -d >actual &&
	echo >>actual &&
	cat <<-EOD >expected &&
	Request #3001 has been accepted by user [1].

	[1] https://aur.archlinux.org/account/user/
	EOD
	test_cmp actual expected
'

test_expect_success 'Test subject and body of request close notifications (auto-accept).' '
	>sendmail.out &&
	cover "$NOTIFY" request-close 0 3001 accepted &&
	grep ^Subject: sendmail.out >actual &&
	cat <<-EOD >expected &&
	Subject: [PRQ#3001] Deletion Request for foobar Accepted
	EOD
	test_cmp actual expected &&
	sed -n "/^\$/,\$p" sendmail.out | base64 -d >actual &&
	echo >>actual &&
	cat <<-EOD >expected &&
	Request #3001 has been accepted automatically by the Arch User
	Repository package request system.
	EOD
	test_cmp actual expected
'

test_expect_success 'Test subject and body of request close notifications with closure comment.' '
	cat <<-EOD | sqlite3 aur.db &&
	UPDATE PackageRequests SET ClosureComment = "This is a test closure comment." WHERE ID = 3001;
	EOD
	>sendmail.out &&
	cover "$NOTIFY" request-close 1 3001 accepted &&
	grep ^Subject: sendmail.out >actual &&
	cat <<-EOD >expected &&
	Subject: [PRQ#3001] Deletion Request for foobar Accepted
	EOD
	test_cmp actual expected &&
	sed -n "/^\$/,\$p" sendmail.out | base64 -d >actual &&
	echo >>actual &&
	cat <<-EOD >expected &&
	Request #3001 has been accepted by user [1]:

	This is a test closure comment.

	[1] https://aur.archlinux.org/account/user/
	EOD
	test_cmp actual expected
'

test_expect_success 'Test subject and body of TU vote reminders.' '
	>sendmail.out &&
	cover "$NOTIFY" tu-vote-reminder 1 &&
	grep ^Subject: sendmail.out | head -1 >actual &&
	cat <<-EOD >expected &&
	Subject: TU Vote Reminder: Proposal 1
	EOD
	test_cmp actual expected &&
	sed -n "/^\$/,\$p" sendmail.out | head -4 | base64 -d >actual &&
	echo >>actual &&
	cat <<-EOD >expected &&
	Please remember to cast your vote on proposal 1 [1]. The voting period
	ends in less than 48 hours.

	[1] https://aur.archlinux.org/tu/?id=1
	EOD
	test_cmp actual expected
'

test_done
