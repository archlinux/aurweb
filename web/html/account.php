<?
include("aur.inc");         # access AUR common functions
include("account_po.inc");  # use some form of this for i18n support
set_lang();                 # this sets up the visitor's language
check_sid();                # see if they're still logged in
html_header();              # print out the HTML header

# Display the standard Account form
# SID: the session id cookie value (if any)
# A: what "form" name to use
# U: value to display for username
# T: value to display for account type
# S: value to display for account suspended
# E: value to display for email address
# P: password value
# C: confirm password value
# R: value to display for RealName
# L: value to display for Language preference
# I: value to display for IRC nick
# N: new package notify value
function display_account_form($SID,$A,$U="",$T="",$S="",$E="",$P="",$C="",$R="",$L="",$I="",$N="") {
	global $SUPPORTED_LANGS;

	print "<form action='/account.php' method='post'>\n";
	print "<input type='hidden' name='Action' value='".$A."'>\n";
	print "<center>\n";
	print "<table border='0' cellpadding='0' cellspacing='0' width='80%'>\n";
	print "<tr><td colspan='2'>&nbsp;</td></tr>\n";

	# figure out what account type the visitor is
	#
	if ($SID) {
		$atype = account_from_sid($SID);
	} else {
		$atype = "";
	}

	print "<tr>";
	print "<td align='left'>".__("Username:")."</td>";
	print "<td align='left'><input type='text' size='30' maxlength='64'";
	print " name='U' value='".$U."'> (".__("required").")</td>";
	print "</tr>\n";

	if ($atype == "Trusted User" || $atype == "Developer") {
		# only TUs or Devs can promote/demote/suspend a user
		#
		print "<tr>";
		print "<td align='left'>".__("Account Type:")."</td>";
		print "<td align='left'><select name=T>\n";
		print "<option value='u'> ".__("Normal user")."\n";
		print "<option value='t'> ".__("Trusted user")."\n";
		if ($atype == "Developer") {
			# only developers can make another account a developer
			#
			print "<option value='d'> ".__("Developer")."\n";
		}
		print "</select></td>";
		print "</tr>\n";

		print "<tr>";
		print "<td align='left'>".__("Account Suspended:")."</td>";
		print "<td align='left'><input type='checkbox' name='S'";
		if ($S) {
			print " checked>";
		} else {
			print ">";
		}
		print "</tr>\n";
	}

	print "<tr>";
	print "<td align='left'>".__("Email Address:")."</td>";
	print "<td align='left'><input type='text' size='30' maxlength='64'";
	print " name='E' value='".$E."'> (".__("required").")</td>";
	print "</tr>\n";

	print "<tr>";
	print "<td align='left'>".__("Password:")."</td>";
	print "<td align='left'><input type='password' size='30' maxlength='32'";
	print " name='P' value='".$P."'> (".__("required").")</td>";
	print "</tr>\n";

	print "<tr>";
	print "<td align='left'>".__("Re-type password:")."</td>";
	print "<td align='left'><input type='password' size='30' maxlength='32'";
	print " name='C' value='".$C."'> (".__("required").")</td>";
	print "</tr>\n";

	print "<tr>";
	print "<td align='left'>".__("Real Name:")."</td>";
	print "<td align='left'><input type='text' size='30' maxlength='32'";
	print " name='R' value='".$R."'></td>";
	print "</tr>\n";

	print "<tr>";
	print "<td align='left'>".__("IRC Nick:")."</td>";
	print "<td align='left'><input type='text' size='30' maxlength='32'";
	print " name='I' value='".$I."'></td>";
	print "</tr>\n";

	print "<tr>";
	print "<td align='left'>".__("Language:")."</td>";
	print "<td align='left'><select name=L>\n";
	while (list($code, $lang) = each($SUPPORTED_LANGS)) {
		if ($L == $code) {
			print "<option value=".$code." selected> ".$lang."\n";
		} else {
			print "<option value=".$code."> ".$lang."\n";
		}
	}
	print "</select></td>";
	print "</tr>\n";

	print "<tr>";
	print "<td align='left'>".__("New Package Notify:")."</td>";
	print "<td align='left'><input type='checkbox' name='N'";
	if ($N) {
		print " checked>";
	} else {
		print ">";
	}
	print "</tr>\n";

	print "<tr><td colspan='2'>&nbsp;</td></tr>\n";
	print "<tr>";
	print "<td>&nbsp;</td>";
	print "<td align='left'>";
	if ($A == "ModifyAccount") {
		print "<input type='submit' value='".__("Update")."'> &nbsp; ";
	} else {
		print "<input type='submit' value='".__("Create")."'> &nbsp; ";
	}
	print "<input type='reset' value='".__("Reset")."'>";
	print "</td>";
	print "</tr>\n";

	print "</table>\n";
	print "</center>\n";
	print "</form>\n";
} # function display_account_form()


# Main page processing here
#
if (isset($_COOKIE["AURSID"])) {
	# visitor is logged in
	#
	$dbh = db_connect();

	if ($_REQUEST["Action"] == "SearchAccounts") {
		# the user has entered search criteria, find any matching accounts
		#
		$HITS_PER_PAGE = 50;
		$OFFSET = 0;

		$q = "SELECT Users.*, AccountTypes.AccountType ";
		$q.= "FROM Users, AccountTypes ";
		$q.= "WHERE AccountTypes.ID = Users.AccountTypeID ";
		if ($_REQUEST["T"] == "u") {
			$q.= "AND AccountTypes.ID = 1 ";
		} elseif ($_REQUEST["T"] == "t") {
			$q.= "AND AccountTypes.ID = 2 ";
		} elseif ($_REQUEST["T"] == "d") {
			$q.= "AND AccountTypes.ID = 3 ";
		}
		if ($_REQUEST["S"]) {
			$q.= "AND Users.Suspended = 1 ";
		}
		if ($_REQUEST["U"]) {
			$q.= "AND Username LIKE '%".mysql_escape_string($_REQUEST["U"])."%' ";
		}
		if ($_REQUEST["E"]) {
			$q.= "AND Email LIKE '%".mysql_escape_string($_REQUEST["E"])."%' ";
		}
		if ($_REQUEST["R"]) {
			$q.= "AND RealName LIKE '%".mysql_escape_string($_REQUEST["R"])."%' ";
		}
		if ($_REQUEST["I"]) {
			$q.= "AND IRCNick LIKE '%".mysql_escape_string($_REQUEST["I"])."%' ";
		}
		$q.= "LIMIT ". $OFFSET . ", " . $HITS_PER_PAGE;
		$result = db_query($q, $dbh);
		if (!$result) {
			print __("No results matched your search criteria.");
		} else {
			print "<center>\n";
			print "<table border='0' cellpadding='0' cellspacing='0' width='90%'>\n";
			print "<tr>";
			print "<td colspan='2'>";
			print "<table border='0' cellpadding='0' cellspacing='0' width='100%'>\n";
			print "<th>".__("Username")."</th>";
			print "<th>".__("Type")."</th>";
			print "<th>".__("Status")."</th>";
			print "<th>".__("Real Name")."</th>";
			print "<th>".__("IRC Nick")."</th>";
			print "<th>".__("Last Voted")."</th>";
			print "</tr>\n";
			$i = 0;
			while ($row = mysql_fetch_assoc($result)) {
				if ($i % 2) {
					print "<tr class='data1'>";
				} else {
					print "<tr class='data2'>";
				}
				print "<td align='center'>".$row["Username"]."</td>";
				print "<td align='center'>".user_type($row["AccountType"])."</td>";
				print "<td align='center'>";
				if ($row["Suspended"]) {
					print __("Suspended");
				} else {
					print __("Active");
				}
				print "</td>";
				print "<td align='left'>";
				$row["RealName"] ? print $row["RealName"] : print "&nbsp;";
				print "</td>";
				print "<td align='left'>";
				$row["IRCNick"] ? print $row["IRCNick"] : print "&nbsp;";
				print "</td>";
				print "<td align='center'>";
				$row["LastVoted"]
						? print date("Ymd", $row["LastVoted"])
						: print __("Never");
				print "</td>";
				print "</tr>\n";
				$i++;
			}
			print "</table>\n";
			print "</td></tr>\n";

			print "<tr>";
			print "<td align='left'>";
			print "<form action='/account.php' method='post'>\n";
			print "<input type='hidden' name='Action' value='SearchPackages'>\n";
			print "<input type='hidden' name='offset' value='more'>\n";
			print "<input type='submit' value='&lt;-- ".__("Less")."'>";
			print "</form>\n";
			print "</td>";
			print "<td align='right'>";
			print "<form action='/account.php' method='post'>\n";
			print "<input type='hidden' name='Action' value='SearchPackages'>\n";
			print "<input type='hidden' name='offset' value='more'>\n";
			print "<input type='submit' value='".__("More")." --&gt;'>";
			print "</form>\n";
			print "</td>";
			print "</tr>\n";
			print "</table>\n";
			print "</center>\n";
		}


	} elseif ($_REQUEST["Action"] == "DisplayAccount") {
		# the user has clicked 'edit', display the account details in a form
		#

	} elseif ($_REQUEST["Action"] == "UpdateAccount") {
		# user is submitting their modifications to an existing account
		#

	} else {
		# display the search page
		#
		print "<form action='/account.php' method='post'>\n";
		print "<input type='hidden' name='Action' value='SearchAccounts'>\n";
		print "<center>\n";
		print "<table border='0' cellpadding='0' cellspacing='0' width='80%'>\n";
		print "<tr><td colspan='2'>&nbsp;</td></tr>\n";

		print "<tr>";
		print "<td align='left'>".__("Username:")."</td>";
		print "<td align='left'><input type='text' size='30' maxlength='64'";
		print " name='U'></td>";
		print "</tr>\n";

		print "<tr>";
		print "<td align='left'>".__("Account Type:")."</td>";
		print "<td align='left'><select name=T>\n";
		print "<option value=''> ".__("Any type")."\n";
		print "<option value='u'> ".__("Normal user")."\n";
		print "<option value='t'> ".__("Trusted user")."\n";
		print "<option value='d'> ".__("Developer")."\n";
		print "</select></td>";
		print "</tr>\n";

		print "<tr>";
		print "<td align='left'>".__("Account Suspended:")."</td>";
		print "<td align='left'><input type='checkbox' name='S'>";
		print "</tr>\n";

		print "<tr>";
		print "<td align='left'>".__("Email Address:")."</td>";
		print "<td align='left'><input type='text' size='30' maxlength='64'";
		print " name='E'></td>";
		print "</tr>\n";

		print "<tr>";
		print "<td align='left'>".__("Real Name:")."</td>";
		print "<td align='left'><input type='text' size='30' maxlength='32'";
		print " name='R'></td>";
		print "</tr>\n";

		print "<tr>";
		print "<td align='left'>".__("IRC Nick:")."</td>";
		print "<td align='left'><input type='text' size='30' maxlength='32'";
		print " name='I'></td>";
		print "</tr>\n";

		print "<tr>";
		print "<td>&nbsp;</td>";
		print "<td align='left'>";
		print "<input type='submit' value='Search'> &nbsp; ";
		print "<input type='reset' value='Reset'></td>";
		print "</tr>\n";

		print "</table>\n";
		print "</center>\n";
		print "</form>\n";
	}

} else {
	# visitor is not logged in
	#
	if ($_REQUEST["Action"] == "NewAccount") {
		# error check and process request for a new account
		#
		$dbh = db_connect();
		$error = "";
		if (!isset($_REQUEST["E"]) || !isset($_REQUEST["P"]) || 
				!isset($_REQUEST["C"])) {
			$error = __("Missing a required field.");
		}
		if (!$error && ($_REQUEST["P"] != $_REQUEST["C"])) {
			$error = __("Password fields do not match.");
		}
		if (!$error && !valid_email($_REQUEST["E"])) {
			$error = __("The email address is invalid.");
		}
		if (!$error && !array_key_exists($_REQUEST["L"], $SUPPORTED_LANGS)) {
			$error = __("Language is not currently supported.");
		}
		if (!$error) {
			# check to see if this username is available
			# NOTE: a race condition exists here if we care...
			#
			$q = "SELECT COUNT(*) AS CNT FROM Users ";
			$q.= "WHERE Username = '".mysql_escape_string($_REQUEST["U"])."'";
			$result = db_query($q, $dbh);
			if ($result) {
				$row = mysql_fetch_array($result);
				if ($row[0]) {
					$error = __("The username, %h%s%h, is already in use.",
							array("<b>", $_REQUEST["U"], "</b>"));
				}
			}
		}
		if (!$error) {
			# check to see if this email address is available
			# NOTE: a race condition exists here if we care...
			#
			$q = "SELECT COUNT(*) AS CNT FROM Users ";
			$q.= "WHERE Email = '".mysql_escape_string($_REQUEST["E"])."'";
			$result = db_query($q, $dbh);
			if ($result) {
				$row = mysql_fetch_array($result);
				if ($row[0]) {
					$error = __("The address, %h%s%h, is already in use.",
							array("<b>", $_REQUEST["E"], "</b>"));
				}
			}
		}
		if ($error) {
			print "<span class='error'>".$error."</span><br/>\n";
			display_account_form("", "NewAccount", "", "",
				$_REQUEST["U"], $_REQUEST["E"], $_REQUEST["R"], $_REQUEST["L"],
				$_REQUEST["I"], $_REQUEST["N"]);
		} else {
			# no errors, go ahead and create the unprivileged user
			#
			$q = "INSERT INTO Users (AccountTypeID, Suspended, Username, Email, ";
			$q.= "Passwd, RealName, LangPreference, IRCNick, NewPkgNotify) ";
			$q.= "VALUES (1, 0, '".mysql_escape_string($_REQUEST["U"])."'";
			$q.= ", '".mysql_escape_string($_REQUEST["E"])."'";
			$q.= ", '".mysql_escape_string($_REQUEST["P"])."'";
			$q.= ", '".mysql_escape_string($_REQUEST["R"])."'";
			$q.= ", '".mysql_escape_string($_REQUEST["L"])."'";
			$q.= ", '".mysql_escape_string($_REQUEST["I"])."'";
			if ($_REQUEST["N"] == "on") {
				$q.= ", 1)";
			} else {
				$q.= ", 0)";
			}
			$result = db_query($q, $dbh);
			if (!$result) {
				print __("Error trying to create account, %h%s%h: %s.",
						array("<b>", $_REQUEST["U"], "</b>", mysql_error($dbh)));
			} else {
				# account created, tell them so.
				#
				print __("The account, %h%s%h, has been successfully created.",
						array("<b>", $_REQUEST["U"], "</b>"));
				print "<p>\n";
				print __("Click on the Home link above to login.");
				print "</p>\n";
			}
		}

	} else {
		# display the account request form
		#
		display_account_form("", "NewAccount");
	}
}

html_footer("\$Id$");
# vim: ts=2 sw=2 noet ft=php
?>
