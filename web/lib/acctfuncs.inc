<?
include_once("acctfuncs_po.inc");

# Display the standard Account form, pass in default values if any
#
function display_account_form($UTYPE,$A,$U="",$T="",$S="",
			$E="",$P="",$C="",$R="",$L="",$I="",$N="",$UID=0) {
	# UTYPE: what user type the form is being displayed for
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
	# UID: Users.ID value in case form is used for editing

	global $SUPPORTED_LANGS;

	print "<form action='/account.php' method='post'>\n";
	print "<input type='hidden' name='Action' value='".$A."'>\n";
	if ($UID) {
		print "<input type='hidden' name='ID' value='".$UID."'>\n";
	}
	print "<center>\n";
	print "<table border='0' cellpadding='0' cellspacing='0' width='80%'>\n";
	print "<tr><td colspan='2'>&nbsp;</td></tr>\n";

	print "<tr>";
	print "<td align='left'>".__("Username").":</td>";
	print "<td align='left'><input type='text' size='30' maxlength='64'";
	print " name='U' value='".$U."'> (".__("required").")</td>";
	print "</tr>\n";

	if ($UTYPE == "Trusted User" || $UTYPE == "Developer") {
		# only TUs or Devs can promote/demote/suspend a user
		#
		print "<tr>";
		print "<td align='left'>".__("Account Type").":</td>";
		print "<td align='left'><select name=T>\n";
		print "<option value='1'";
		$T == "User" ? print " selected>" : print ">";
		print	__("Normal user")."\n";
		print "<option value='2'";
		$T == "Trusted User" ? print " selected>" : print ">";
		print __("Trusted user")."\n";
		if ($UTYPE == "Developer") {
			# only developers can make another account a developer
			#
			print "<option value='3'";
			$T == "Developer" ? print " selected>" : print ">";
			print __("Developer")."\n";
		}
		print "</select></td>";
		print "</tr>\n";

		print "<tr>";
		print "<td align='left'>".__("Account Suspended").":</td>";
		print "<td align='left'><input type='checkbox' name='S'";
		if ($S) {
			print " checked>";
		} else {
			print ">";
		}
		print "</tr>\n";
	}

	print "<tr>";
	print "<td align='left'>".__("Email Address").":</td>";
	print "<td align='left'><input type='text' size='30' maxlength='64'";
	print " name='E' value='".$E."'> (".__("required").")</td>";
	print "</tr>\n";

	print "<tr>";
	print "<td align='left'>".__("Password").":</td>";
	print "<td align='left'><input type='password' size='30' maxlength='32'";
	print " name='P' value='".$P."'>";
	if ($TYPE == "new") {
		print "	(".__("required").")";
	}
	print "</td></tr>\n";

	print "<tr>";
	print "<td align='left'>".__("Re-type password").":</td>";
	print "<td align='left'><input type='password' size='30' maxlength='32'";
	print " name='C' value='".$C."'>";
	if ($TYPE == "new") {
		print "	(".__("required").")";
	}
	print "</td></tr>\n";

	print "<tr>";
	print "<td align='left'>".__("Real Name").":</td>";
	print "<td align='left'><input type='text' size='30' maxlength='32'";
	print " name='R' value='".$R."'></td>";
	print "</tr>\n";

	print "<tr>";
	print "<td align='left'>".__("IRC Nick").":</td>";
	print "<td align='left'><input type='text' size='30' maxlength='32'";
	print " name='I' value='".$I."'></td>";
	print "</tr>\n";

	print "<tr>";
	print "<td align='left'>".__("Language").":</td>";
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
	print "<td align='left'>".__("New Package Notify").":</td>";
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
	if ($A == "UpdateAccount") {
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
	return;
} # function display_account_form()


# process form input from a new/edit account form
#
function process_account_form($UTYPE,$TYPE,$A,$U="",$T="",$S="",$E="",
			$P="",$C="",$R="",$L="",$I="",$N="",$UID=0) {
	# UTYPE: The user's account type
	# TYPE: either "edit" or "new"
	# A: what parent "form" name to use
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
	# UID: database Users.ID value

	# error check and process request for a new/modified account
	#
	global $SUPPORTED_LANGS;

	$dbh = db_connect();
	$error = "";
	if (!isset($E) || !isset($U)) {
		$error = __("Missing a required field.");
	}
	if ($TYPE == "new") {
		# they need password fields for this type of action
		#
		if (!isset($P) || !isset($C)) {
			$error = __("Missing a required field.");
		}
	} else {
		if (!$UID) {
			$error = __("Missing User ID");
		}
	}
	if (!$error && $P && $C && ($P != $C)) {
		$error = __("Password fields do not match.");
	}
	if (!$error && !valid_email($E)) {
		$error = __("The email address is invalid.");
	}
	if ($UTYPE == "Trusted User" && $T == 3) {
		$error = __("A Trusted User cannot assign Developer status.");
	}
	if (!$error && !array_key_exists($L, $SUPPORTED_LANGS)) {
		$error = __("Language is not currently supported.");
	}
	if (!$error) {
		# check to see if this username is available
		# NOTE: a race condition exists here if we care...
		#
		$q = "SELECT COUNT(*) AS CNT FROM Users ";
		$q.= "WHERE Username = '".mysql_escape_string($U)."'";
		if ($TYPE == "edit") {
			$q.= " AND ID != ".intval($UID);
		}
		$result = db_query($q, $dbh);
		if ($result) {
			$row = mysql_fetch_array($result);
			if ($row[0]) {
				$error = __("The username, %h%s%h, is already in use.",
						array("<b>", $U, "</b>"));
			}
		}
	}
	if (!$error) {
		# check to see if this email address is available
		# NOTE: a race condition exists here if we care...
		#
		$q = "SELECT COUNT(*) AS CNT FROM Users ";
		$q.= "WHERE Email = '".mysql_escape_string($E)."'";
		if ($TYPE == "edit") {
			$q.= " AND ID != ".intval($UID);
		}
		$result = db_query($q, $dbh);
		if ($result) {
			$row = mysql_fetch_array($result);
			if ($row[0]) {
				$error = __("The address, %h%s%h, is already in use.",
						array("<b>", $E, "</b>"));
			}
		}
	}
	if ($error) {
		print "<span class='error'>".$error."</span><br/>\n";
		display_account_form($UTYPE, $A, $U, $T, $S, $E, "", "",
				$R, $L, $I, $N, $UID);
	} else {
		if ($TYPE == "new") {
			# no errors, go ahead and create the unprivileged user
			#
			$q = "INSERT INTO Users (AccountTypeID, Suspended, Username, Email, ";
			$q.= "Passwd, RealName, LangPreference, IRCNick, NewPkgNotify) ";
			$q.= "VALUES (1, 0, '".mysql_escape_string($U)."'";
			$q.= ", '".mysql_escape_string($E)."'";
			$q.= ", '".mysql_escape_string($P)."'";
			$q.= ", '".mysql_escape_string($R)."'";
			$q.= ", '".mysql_escape_string($L)."'";
			$q.= ", '".mysql_escape_string($I)."'";
			if ($N) {
				$q.= ", 1)";
			} else {
				$q.= ", 0)";
			}
			$result = db_query($q, $dbh);
			if (!$result) {
				print __("Error trying to create account, %h%s%h: %s.",
						array("<b>", $U, "</b>", mysql_error($dbh)));
			} else  {
				# account created/modified, tell them so.
				#
				print __("The account, %h%s%h, has been successfully created.",
						array("<b>", $U, "</b>"));
				print "<p>\n";
				print __("Click on the Home link above to login.");
				print "</p>\n";
			}

		} else {
			# no errors, go ahead and modify the user account
			#
			$q = "UPDATE Users SET ";
			$q.= "Username = '".mysql_escape_string($U)."'";
			if ($T) {
				$q.= ", AccountTypeID = ".intval($T);
			}
			if ($S) {
				$q.= ", Suspended = 1";
			} else {
				$q.= ", Suspended = 0";
			}
			$q.= ", Email = '".mysql_escape_string($E)."'";
			if ($P) {
				$q.= ", Passwd = '".mysql_escape_string($P)."'";
			}
			$q.= ", RealName = '".mysql_escape_string($R)."'";
			$q.= ", LangPreference = '".mysql_escape_string($L)."'";
			$q.= ", IRCNick = '".mysql_escape_string($I)."'";
			$q.= ", NewPkgNotify = ";
			if ($N) {
				$q.= "1 ";
			} else {
				$q.= "0 ";
			}
			$q.= "WHERE ID = ".intval($UID);
			$result = db_query($q, $dbh);
			if (!$result) {
				print __("Error trying to modify account, %h%s%h: %s.",
						array("<b>", $U, "</b>", mysql_error($dbh)));
			} else {
				print __("The account, %h%s%h, has been successfully modified.",
						array("<b>", $U, "</b>"));
			}
		}
	}
	return;
}

# search existing accounts
#
function search_accounts_form() {
	print "<form action='/account.php' method='post'>\n";
	print "<input type='hidden' name='Action' value='SearchAccounts'>\n";
	print "<center>\n";
	print "<table border='0' cellpadding='0' cellspacing='0' width='80%'>\n";
	print "<tr><td colspan='2'>&nbsp;</td></tr>\n";

	print "<tr>";
	print "<td align='left'>".__("Username").":</td>";
	print "<td align='left'><input type='text' size='30' maxlength='64'";
	print " name='U'></td>";
	print "</tr>\n";

	print "<tr>";
	print "<td align='left'>".__("Account Type").":</td>";
	print "<td align='left'><select name=T>\n";
	print "<option value=''> ".__("Any type")."\n";
	print "<option value='u'> ".__("Normal user")."\n";
	print "<option value='t'> ".__("Trusted user")."\n";
	print "<option value='d'> ".__("Developer")."\n";
	print "</select></td>";
	print "</tr>\n";

	print "<tr>";
	print "<td align='left'>".__("Account Suspended").":</td>";
	print "<td align='left'><input type='checkbox' name='S'>";
	print "</tr>\n";

	print "<tr>";
	print "<td align='left'>".__("Email Address").":</td>";
	print "<td align='left'><input type='text' size='30' maxlength='64'";
	print " name='E'></td>";
	print "</tr>\n";

	print "<tr>";
	print "<td align='left'>".__("Real Name").":</td>";
	print "<td align='left'><input type='text' size='30' maxlength='32'";
	print " name='R'></td>";
	print "</tr>\n";

	print "<tr>";
	print "<td align='left'>".__("IRC Nick").":</td>";
	print "<td align='left'><input type='text' size='30' maxlength='32'";
	print " name='I'></td>";
	print "</tr>\n";

	print "<tr>";
	print "<td align='left'>".__("Sort by").":</td>";
	print "<td align='left'><select name=SB>\n";
	print "<option value='u'> ".__("Username")."\n";
	print "<option value='t'> ".__("Account Type")."\n";
	print "<option value='r'> ".__("Real Name")."\n";
	print "<option value='i'> ".__("IRC Nick")."\n";
	print "<option value='v'> ".__("Last vote")."\n";
	print "</select></td>";
	print "</tr>\n";

	print "<tr>";
	print "<td>&nbsp;</td>";
	print "<td align='left'>&nbsp;<br/>&nbsp;&nbsp;&nbsp;&nbsp;";
	print "<input type='submit' value='".__("Search'")."> &nbsp; ";
	print "<input type='reset' value='".__("Reset")."'></td>";
	print "</tr>\n";

	print "</table>\n";
	print "</center>\n";
	print "</form>\n";
	return;
}


# search results page
#
function search_results_page($UTYPE,$O=0,$SB="",$U="",$T="",
		$S="",$E="",$R="",$I="") {
	# UTYPE: what account type the user belongs to
	# O: what row offset we're at
	# SB: how to sort the results
	# U: value to display for username
	# T: value to display for account type
	# S: value to display for account suspended
	# E: value to display for email address
	# R: value to display for RealName
	# I: value to display for IRC nick

	$HITS_PER_PAGE = 50;
	if ($O) {
		$OFFSET = intval($O);
	} else {
		$OFFSET = 0;
	}
	if ($OFFSET < 0) {
		$OFFSET = 0;
	}
	$search_vars = array();

	$q = "SELECT Users.*, AccountTypes.AccountType ";
	$q.= "FROM Users, AccountTypes ";
	$q.= "WHERE AccountTypes.ID = Users.AccountTypeID ";
	if ($T == "u") {
		$q.= "AND AccountTypes.ID = 1 ";
		$search_vars[] = "T";
	} elseif ($T == "t") {
		$q.= "AND AccountTypes.ID = 2 ";
		$search_vars[] = "T";
	} elseif ($T == "d") {
		$q.= "AND AccountTypes.ID = 3 ";
		$search_vars[] = "T";
	}
	if ($S) {
		$q.= "AND Users.Suspended = 1 ";
		$search_vars[] = "S";
	}
	if ($U) {
		$q.= "AND Username LIKE '%".mysql_escape_string($U)."%' ";
		$search_vars[] = "U";
	}
	if ($E) {
		$q.= "AND Email LIKE '%".mysql_escape_string($E)."%' ";
		$search_vars[] = "E";
	}
	if ($R) {
		$q.= "AND RealName LIKE '%".mysql_escape_string($R)."%' ";
		$search_vars[] = "R";
	}
	if ($I) {
		$q.= "AND IRCNick LIKE '%".mysql_escape_string($I)."%' ";
		$search_vars[] = "I";
	}
	switch ($SB) {
		case 't':
			$q.= "ORDER BY AccountTypeID, Username ";
			break;
		case 'r':
			$q.= "ORDER BY RealName, AccountTypeID ";
			break;
		case 'i':
			$q.= "ORDER BY IRCNick, AccountTypeID ";
			break;
		case 'v':
			$q.= "ORDER BY LastVoted, Username ";
			break;
		default:
			$q.= "ORDER BY Username, AccountTypeID ";
			break;
	}
	$search_vars[] = "SB";
	$q.= "LIMIT ". $OFFSET . ", " . $HITS_PER_PAGE;
	$result = db_query($q, $dbh);
	if (!$result) {
		print __("No results matched your search criteria.");
	} else {
		$num_rows = mysql_num_rows($result);
		if ($num_rows) {
			print "<center>\n";
			print "<table border='0' cellpadding='0'";
			print " cellspacing='0' width='90%'>\n";
			print "<tr>";
			print "<td colspan='2'>";
			print "<table border='0' cellpadding='0'";
			print " cellspacing='0' width='100%'>\n";
			print "<th class='header'>";
			print "<span class='f2'>".__("Username")."</span></th>";
			print "<th class='header'>";
			print "<span class='f2'>".__("Type")."</span></th>";
			print "<th class='header'>";
			print "<span class='f2'>".__("Status")."</span></th>";
			print "<th class='header'>";
			print "<span class='f2'>".__("Real Name")."</span></th>";
			print "<th class='header'>";
			print "<span class='f2'>".__("IRC Nick")."</span></th>";
			print "<th class='header'>";
			print "<span class='f2'>".__("Last Voted")."</span></th>";
			print "<th class='header'>";
			print "<span class='f2'>".__("Edit Account")."</span></th>";
			print "</tr>\n";
			$i = 0;
			while ($row = mysql_fetch_assoc($result)) {
				if ($i % 2) {
					$c = "data1";
				} else {
					$c = "data2";
				}
				print "<tr>";
				print "<td class='".$c."'>";
				print "<span class='f5'>".$row["Username"]."</span></td>";
				print "<td class='".$c."'>";
				print "<span class='f5'>".$row["AccountType"];
				print "</span></td>";
				print "<td class='".$c."'><span class='f5'>";
				if ($row["Suspended"]) {
					print __("Suspended");
				} else {
					print __("Active");
				}
				print "</span></td>";
				print "<td class='".$c."'><span class='f5'>";
				$row["RealName"] ? print $row["RealName"] : print "&nbsp;";
				print "</span></td>";
				print "<td class='".$c."'><span class='f5'>";
				$row["IRCNick"] ? print $row["IRCNick"] : print "&nbsp;";
				print "</span></td>";
				print "<td class='".$c."'><span class='f5'>";
				$row["LastVoted"]
						? print date("Ymd", $row["LastVoted"])
						: print __("Never");
				print "</span></td>";
				print "<td class='".$c."'><span class='f5'>";
				if ($UTYPE == "Trusted User" && $row["AccountType"] == "Developer") {
					# TUs can't edit devs
					#
					print "&nbsp;</span></td>";
				} else {
					$edit_url = "/account.php?Action=DisplayAccount&ID=".$row["ID"];
					print "<a href='".$edit_url . "'>";
					print "Edit</a></span></td>";
				}
				print "</tr>\n";
				$i++;
			}
			print "</table>\n";
			print "</td></tr>\n";

			print "<tr>";
			print "<td align='left'>";
			print "<form action='/account.php' method='post'>\n";
			print "<input type='hidden' name='Action' value='SearchAccounts'>\n";
			print "<input type='hidden' name='O'";
			print " value='".($OFFSET-$HITS_PER_PAGE)."'>\n";
			reset($search_vars);
			while (list($k, $ind) = each($search_vars)) {
				print "<input type='hidden' name='".$ind."'";
				print " value='".${$ind}."'>\n";
			}
			print "<input type='submit' value='&lt;-- ".__("Less")."'>";
			print "</form>\n";
			print "</td>";
			print "<td align='right'>";
			print "<form action='/account.php' method='post'>\n";
			print "<input type='hidden' name='Action' value='SearchAccounts'>\n";
			print "<input type='hidden' name='O'";
			print " value='".($OFFSET+$HITS_PER_PAGE)."'>\n";
			reset($search_vars);
			while (list($k, $ind) = each($search_vars)) {
				print "<input type='hidden' name='".$ind."'";
				print " value='".${$ind}."'>\n";
			}
			print "<input type='submit' value='".__("More")." --&gt;'>";
			print "</form>\n";
			print "</td>";
			print "</tr>\n";
			print "</table>\n";
			print "</center>\n";
		} else {
			print "<center>\n";
			print __("No more results to display.");
			print "</center>\n";
		}
	}
	return;
}

# vim: ts=2 sw=2 noet ft=php
?>
