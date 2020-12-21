#!/bin/sh

test_description='tuvotereminder tests'

. "$(dirname "$0")/setup.sh"

test_expect_success 'Test Trusted User vote reminders.' '
	now=$(date -d now +%s) &&
	tomorrow=$(date -d tomorrow +%s) &&
	threedays=$(date -d "3 days" +%s) &&
	cat <<-EOD | sqlite3 aur.db &&
	INSERT INTO TU_VoteInfo (ID, Agenda, User, Submitted, End, Quorum, SubmitterID) VALUES (1, "Lorem ipsum.", "user", 0, $now, 0.00, 2);
	INSERT INTO TU_VoteInfo (ID, Agenda, User, Submitted, End, Quorum, SubmitterID) VALUES (2, "Lorem ipsum.", "user", 0, $tomorrow, 0.00, 2);
	INSERT INTO TU_VoteInfo (ID, Agenda, User, Submitted, End, Quorum, SubmitterID) VALUES (3, "Lorem ipsum.", "user", 0, $tomorrow, 0.00, 2);
	INSERT INTO TU_VoteInfo (ID, Agenda, User, Submitted, End, Quorum, SubmitterID) VALUES (4, "Lorem ipsum.", "user", 0, $threedays, 0.00, 2);
	EOD
	>sendmail.out &&
	cover "$TUVOTEREMINDER" &&
	grep -q "Proposal 2" sendmail.out &&
	grep -q "Proposal 3" sendmail.out &&
	test_must_fail grep -q "Proposal 1" sendmail.out &&
	test_must_fail grep -q "Proposal 4" sendmail.out
'

test_expect_success 'Check that only TUs who did not vote receive reminders.' '
	cat <<-EOD | sqlite3 aur.db &&
	INSERT INTO TU_Votes (VoteID, UserID) VALUES (1, 2);
	INSERT INTO TU_Votes (VoteID, UserID) VALUES (2, 2);
	INSERT INTO TU_Votes (VoteID, UserID) VALUES (3, 2);
	INSERT INTO TU_Votes (VoteID, UserID) VALUES (4, 2);
	INSERT INTO TU_Votes (VoteID, UserID) VALUES (1, 7);
	INSERT INTO TU_Votes (VoteID, UserID) VALUES (3, 7);
	INSERT INTO TU_Votes (VoteID, UserID) VALUES (2, 8);
	INSERT INTO TU_Votes (VoteID, UserID) VALUES (4, 8);
	INSERT INTO TU_Votes (VoteID, UserID) VALUES (1, 9);
	EOD
	>sendmail.out &&
	cover "$TUVOTEREMINDER" &&
	cat <<-EOD >expected &&
	Subject: TU Vote Reminder: Proposal 2
	To: tu2@localhost
	Subject: TU Vote Reminder: Proposal 2
	To: tu4@localhost
	Subject: TU Vote Reminder: Proposal 3
	To: tu3@localhost
	Subject: TU Vote Reminder: Proposal 3
	To: tu4@localhost
	EOD
	grep "^\(Subject\|To\)" sendmail.out >sendmail.parts &&
	test_cmp sendmail.parts expected
'

test_done
