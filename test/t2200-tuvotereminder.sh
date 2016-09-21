#!/bin/sh

test_description='tuvotereminder tests'

. ./setup.sh

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
	>notify.out &&
	"$TUVOTEREMINDER" &&
	cat <<-EOD >expected &&
	tu-vote-reminder 2
	tu-vote-reminder 3
	EOD
	test_cmp notify.out expected
'

test_done
