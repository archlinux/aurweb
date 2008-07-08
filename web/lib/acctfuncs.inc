<?php
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
	if ($A != "UpdateAccount") {
		print "	(".__("required").")";
	}
	print "</td></tr>\n";

	print "<tr>";
	print "<td align='left'>".__("Re-type password").":</td>";
	print "<td align='left'><input type='password' size='30' maxlength='32'";
	print " name='C' value='".$C."'>";
	if ($A != "UpdateAccount") {
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

	reset($SUPPORTED_LANGS);
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
		print "<input type='submit' class='button'";
	 	print "	value='".__("Update")."'> &nbsp; ";
	} else {
		print "<input type='submit' class='button'";
		print " value='".__("Create")."'> &nbsp; ";
	}
	print "<input type='reset' class='button' value='".__("Reset")."'>";
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

	if(isset($_COOKIE['AURSID']))
		$editor_user = 	uid_from_sid($_COOKIE['AURSID']);
	else
		$editor_user = null;

	$dbh = db_connect();
	$error = "";
	if (empty($E) || empty($U)) {
		$error = __("Missing a required field.");
	}
	
	if ($TYPE == "new") {
		# they need password fields for this type of action
		#
		if (empty($P) || empty($C)) {
			$error = __("Missing a required field.");
		}
	} else {
		if (!$UID) {
			$error = __("Missing User ID");
		}
	}

  if (!$error && !valid_username($U) && !user_is_privileged($editor_user))
    $error = __("The username is invalid.") . "<ul>\n"
			."<li>" . __("It must be between %s and %s characters long", 
			USERNAME_MIN_LEN,  USERNAME_MAX_LEN )
			. "</li>"
      . "<li>" . __("Start and end with a letter or number") . "</li>"
			. "<li>" . __("Can contain only one period, underscore or hyphen.")
			. "</li>\n</ul>";

	if (!$error && $P && $C && ($P != $C)) {
		$error = __("Password fields do not match.");
	}
	if (!$error && $P != '' && !good_passwd($P))
		$error = 
				__("Your password must be at least %s characters.",PASSWD_MIN_LEN);

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
		$q.= "WHERE Username = '".mysql_real_escape_string($U)."'";
		if ($TYPE == "edit") {
			$q.= " AND ID != ".intval($UID);
		}
		$result = db_query($q, $dbh);
		if ($result) {
			$row = mysql_fetch_array($result);
			if ($row[0]) {
				$error = __("The username, %h%s%h, is already in use.",
				 	"<b>", $U, "</b>");
			}
		}
	}
	if (!$error) {
		# check to see if this email address is available
		# NOTE: a race condition exists here if we care...
		#
		$q = "SELECT COUNT(*) AS CNT FROM Users ";
		$q.= "WHERE Email = '".mysql_real_escape_string($E)."'";
		if ($TYPE == "edit") {
			$q.= " AND ID != ".intval($UID);
		}
		$result = db_query($q, $dbh);
		if ($result) {
			$row = mysql_fetch_array($result);
			if ($row[0]) {
				$error = __("The address, %h%s%h, is already in use.",
						"<b>", $E, "</b>");
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
			
			#md5hash the password
			$P = md5($P);
			$q = "INSERT INTO Users (AccountTypeID, Suspended, Username, Email, ";
			$q.= "Passwd, RealName, LangPreference, IRCNick, NewPkgNotify) ";
			$q.= "VALUES (1, 0, '".mysql_real_escape_string($U)."'";
			$q.= ", '".mysql_real_escape_string($E)."'";
			$q.= ", '".mysql_real_escape_string($P)."'";
			$q.= ", '".mysql_real_escape_string($R)."'";
			$q.= ", '".mysql_real_escape_string($L)."'";
			$q.= ", '".mysql_real_escape_string($I)."'";
			if ($N) {
				$q.= ", 1)";
			} else {
				$q.= ", 0)";
			}
			$result = db_query($q, $dbh);
			if (!$result) {
				print __("Error trying to create account, %h%s%h: %s.",
						"<b>", $U, "</b>", mysql_error($dbh));
			} else {
				# account created/modified, tell them so.
				#
				print __("The account, %h%s%h, has been successfully created.",
						"<b>", $U, "</b>");
				print "<p>\n";
				print __("Click on the Home link above to login.");
				print "</p>\n";
			}

		} else {
			# no errors, go ahead and modify the user account
			#

			#md5 hash the password
			$q = "UPDATE Users SET ";
			$q.= "Username = '".mysql_real_escape_string($U)."'";
			if ($T) {
				$q.= ", AccountTypeID = ".intval($T);
			}
			if ($S) {
				$q.= ", Suspended = 1";
			} else {
				$q.= ", Suspended = 0";
			}
			$q.= ", Email = '".mysql_real_escape_string($E)."'";
			if ($P) {
				$q.= ", Passwd = '".mysql_real_escape_string(md5($P))."'";
			}
			$q.= ", RealName = '".mysql_real_escape_string($R)."'";
			$q.= ", LangPreference = '".mysql_real_escape_string($L)."'";
			$q.= ", IRCNick = '".mysql_real_escape_string($I)."'";
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
						"<b>", $U, "</b>", mysql_error($dbh));
			} else {
				print __("The account, %h%s%h, has been successfully modified.",
						"<b>", $U, "</b>");
			}
		}
	}
	return;
}

# search existing accounts
#
function search_accounts_form() {
	include("search_accounts_form.php");
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
		$q.= "AND Username LIKE '%".mysql_real_escape_string($U)."%' ";
		$search_vars[] = "U";
	}
	if ($E) {
		$q.= "AND Email LIKE '%".mysql_real_escape_string($E)."%' ";
		$search_vars[] = "E";
	}
	if ($R) {
		$q.= "AND RealName LIKE '%".mysql_real_escape_string($R)."%' ";
		$search_vars[] = "R";
	}
	if ($I) {
		$q.= "AND IRCNick LIKE '%".mysql_real_escape_string($I)."%' ";
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
				print "<span class='f5'><a href='/packages.php?SeB=m&K=".$row["Username"]."'>".$row["Username"]."</a></span></td>";
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
			print "<input type='submit' class='button'";
			print " value='&lt;-- ".__("Less")."'>";
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
			print "<input type='submit' class='button'";
			print " value='".__("More")." --&gt;'>";
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

# Display non-editable account info
#
function display_account_info($U="",$T="",
			$E="",$R="",$I="") {
	# U: value to display for username
	# T: value to display for account type
	# E: value to display for email address
	# R: value to display for RealName
	# I: value to display for IRC nick

	global $SUPPORTED_LANGS;

	print "<center>\n";
	print "<table border='0' cellpadding='0' cellspacing='0' width='33%'>\n";
	print "  <tr>\n";
	print "    <td colspan='2'>&nbsp;</td>\n";
	print "  </tr>\n";

	print "  <tr>\n";
	print "    <td align='left'>".__("Username").":</td>\n";
	print "    <td align='left'>".$U."</td>\n";
	print "  </tr>\n";
	
	print "  <tr>\n";
	print "    <td align='left'>".__("Account Type").":</td>\n";
	print "    <td align='left'>";
	if ($T == "User") {
		print __("User");
	} elseif ($T == "Trusted User") {
		print __("Trusted User");
	}	elseif ($T == "Developer") {
		print __("Developer");
	}
	print "</td>\n";
	
	print "  <tr>\n";
	print "    <td align='left'>".__("Email Address").":</td>\n";
	print "    <td align='left'><a href='mailto:".$E."'>".$E."</a></td>\n";
	print "  </tr>\n";

	print "  <tr>\n";
	print "    <td align='left'>".__("Real Name").":</td>\n";
	print "    <td align='left'>".$R."</td>\n";
	print "  </tr>\n";

	print "  <tr>\n";
	print "    <td align='left'>".__("IRC Nick").":</td>\n";
	print "    <td align='left'>".$I."</td>\n";
	print "  </tr>\n";

	print "  <tr>\n";
	print "    <td colspan='2'><a href='/packages.php?K=".$U."&SeB=m'>".__("View this user's packages")."</a></td>\n";
	print "  </tr>\n";

	print "</table>\n";
	print "</center>\n";
	return;
}

/*
 * Returns SID (Session ID) and error (error message) in an array
 * SID of 0 means login failed.
 */
function try_login() {
	$login_error = ""; 
	$new_sid = "";
	$userID = null;

	if ( isset($_REQUEST['user']) || isset($_REQUEST['passwd']) ) {


		$userID = valid_user($_REQUEST['user']);

		if ( user_suspended( $userID ) ) {
			$login_error = "Account Suspended.";
		}
		elseif ( $userID && isset($_REQUEST['passwd'])
		  && valid_passwd($userID, $_REQUEST['passwd']) ) {

			$logged_in = 0;
			$num_tries = 0;

			# Account looks good.  Generate a SID and store it.
			#

			$dbh = db_connect();
			while (!$logged_in && $num_tries < 5) {
				$new_sid = new_sid();
				$q = "INSERT INTO Sessions (UsersID, SessionID, LastUpdateTS)"
				  ." VALUES ( $userID, '" . $new_sid . "', UNIX_TIMESTAMP())";
				$result = db_query($q, $dbh);
				# Query will fail if $new_sid is not unique
				#
				if ($result) {
					$logged_in = 1;
					break;
				}
				$num_tries++;
		        }
			if ($logged_in) {
				# set our SID cookie

				if ($_POST['remember_me'] == "on")
					# Set cookies for 30 days.
					$cookie_time = time() + (60 * 60 * 24 * 30);
				else
					$cookie_time = 0;
				setcookie("AURSID", $new_sid, $cookie_time, "/");
#				header("Location: /index.php");
				header("Location: " . $_SERVER['PHP_SELF'].'?'.$_SERVER['QUERY_STRING']);
				$login_error = "";

			}
			else {
				$login_error = "Error trying to generate session id.";
			}
		}
		else {
			$login_error = "Bad username or password.";
		}
	}
	return array('SID' => $new_sid, 'error' => $login_error);
}

/*
 * Only checks if the name itself is valid
 * Longer or equal to USERNAME_MIN_LEN
 * Shorter or equal to USERNAME_MAX_LEN
 * Starts and ends with a letter or number
 * Contains at most ONE dot, hyphen, or underscore
 * Returns the username if it is valid
 * Returns nothing if it isn't valid
 */
function valid_username( $user )
{

	#Is it non-empty?
	if (!empty($user)) {
		
		#Is username at not too short or too long?
		if ( strlen($user) >= USERNAME_MIN_LEN &&
		  strlen($user) <= USERNAME_MAX_LEN ) {
			
			$user = strtolower($user);
			#Does username:
			# start and end with a letter or number
			# contain only letters and numbers,
			#  and at most has one dash, period, or underscore
			if ( preg_match("/^[a-z0-9]+[.\-_]?[a-z0-9]+$/", $user) ) {
				#All is good return the username
				return $user;
			}
		}
	}
	
	return;
}

/*
 * Checks if the username is valid and if it exists in the database
 * Returns the username ID or nothing
 */
function valid_user( $user )
{
	/*	if ( $user = valid_username($user) ) { */
	if ( $user ) {
		$dbh = db_connect();
		$q = "SELECT ID FROM Users WHERE Username = '"
			. mysql_real_escape_string($user). "'";

		$result = mysql_fetch_row(db_query($q, $dbh));
		#Is the username in the database? 
		if ($result[0]) {
			return $result[0];
		}
	}
	return;
}

function good_passwd( $passwd )
{
	if ( strlen($passwd) >= PASSWD_MIN_LEN ) {
		return true;
	}
	return false;
}

/* Verifies that the password is correct for the userID specified.
 * Returns true or false
 */
function valid_passwd( $userID, $passwd )
{
	if ( strlen($passwd) > 0 ) {
		$dbh = db_connect();
		$q = "SELECT ID FROM Users".
		  " WHERE ID = '$userID'" .
		  " AND Passwd = '" . md5($passwd) . "'";

		$result = mysql_fetch_row(db_query($q, $dbh));
		if ($result[0]) {
			#is it the right password?
			return true;
		}
	}
	return false;
}

/*
 * Is the user account suspended?
 */
function user_suspended( $id )
{
	$dbh = db_connect();
	$q = "SELECT Suspended FROM Users WHERE ID = '$id'";
	$result = mysql_fetch_row(db_query($q, $dbh));
	if ($result[0] == 1 ) {
		return true;
	}
	return false;
}

/*
 * This should be expanded to return something
 * TODO: Handle orphaning of user's packages
 */
function user_delete( $id )
{
	$dbh = db_connect();
	$q = "DELETE FROM Users WHERE ID = '$id'";
	$result = mysql_fetch_row(db_query($q, $dbh));
	return;
}

/*
 * A different way of determining a user's privileges
 * rather than account_from_sid()
 */
function user_is_privileged( $id )
{
	$dbh = db_connect();
	$q = "SELECT AccountTypeID FROM Users WHERE ID = '$id'";
	$result = mysql_fetch_row(db_query($q, $dbh));
	if( $result[0] > 1)
		return $result[0];
	return 0;

}

?>
