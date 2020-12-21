#!/bin/sh

test_description='usermaint tests'

. "$(dirname "$0")/setup.sh"

test_expect_success 'Test removal of login IP addresses.' '
	now=$(date -d now +%s) &&
	threedaysago=$(date -d "3 days ago" +%s) &&
	tendaysago=$(date -d "10 days ago" +%s) &&
	cat <<-EOD | sqlite3 aur.db &&
	UPDATE Users SET LastLogin = $threedaysago, LastLoginIPAddress = "1.2.3.4" WHERE ID = 1;
	UPDATE Users SET LastLogin = $tendaysago, LastLoginIPAddress = "2.3.4.5" WHERE ID = 2;
	UPDATE Users SET LastLogin = $now, LastLoginIPAddress = "3.4.5.6" WHERE ID = 3;
	UPDATE Users SET LastLogin = 0, LastLoginIPAddress = "4.5.6.7" WHERE ID = 4;
	UPDATE Users SET LastLogin = 0, LastLoginIPAddress = "5.6.7.8" WHERE ID = 5;
	UPDATE Users SET LastLogin = $tendaysago, LastLoginIPAddress = "6.7.8.9" WHERE ID = 6;
	EOD
	cover "$USERMAINT" &&
	cat <<-EOD >expected &&
	1.2.3.4
	3.4.5.6
	EOD
	echo "SELECT LastLoginIPAddress FROM Users WHERE LastLoginIPAddress IS NOT NULL;" | sqlite3 aur.db >actual &&
	test_cmp actual expected
'

test_expect_success 'Test removal of SSH login IP addresses.' '
	now=$(date -d now +%s) &&
	threedaysago=$(date -d "3 days ago" +%s) &&
	tendaysago=$(date -d "10 days ago" +%s) &&
	cat <<-EOD | sqlite3 aur.db &&
	UPDATE Users SET LastSSHLogin = $now, LastSSHLoginIPAddress = "1.2.3.4" WHERE ID = 1;
	UPDATE Users SET LastSSHLogin = $threedaysago, LastSSHLoginIPAddress = "2.3.4.5" WHERE ID = 2;
	UPDATE Users SET LastSSHLogin = $tendaysago, LastSSHLoginIPAddress = "3.4.5.6" WHERE ID = 3;
	UPDATE Users SET LastSSHLogin = 0, LastSSHLoginIPAddress = "4.5.6.7" WHERE ID = 4;
	UPDATE Users SET LastSSHLogin = 0, LastSSHLoginIPAddress = "5.6.7.8" WHERE ID = 5;
	UPDATE Users SET LastSSHLogin = $tendaysago, LastSSHLoginIPAddress = "6.7.8.9" WHERE ID = 6;
	EOD
	cover "$USERMAINT" &&
	cat <<-EOD >expected &&
	1.2.3.4
	2.3.4.5
	EOD
	echo "SELECT LastSSHLoginIPAddress FROM Users WHERE LastSSHLoginIPAddress IS NOT NULL;" | sqlite3 aur.db >actual &&
	test_cmp actual expected
'

test_done
